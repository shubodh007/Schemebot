from __future__ import annotations

import asyncio
import json
import math
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.base import Message
from app.ai.providers.factory import ProviderFactory
from app.ai.rag.chunker import TextChunker
from app.ai.rag.embedder import Embedder
from app.core.database import async_session_factory
from app.core.logging import logger
from app.models.document import DocumentChunk


class Retriever:
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
    ) -> None:
        self.embedder = embedder or Embedder()
        self.chunker = TextChunker()

    async def retrieve(
        self,
        query: str,
        top_k: int = 6,
        filter_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        query_vec = await self.embedder.embed_query(query)

        hyde_query = await self._expand_query(query)
        hyde_vec = await self.embedder.embed_query(hyde_query)

        async with async_session_factory() as session:
            semantic_results = await self._semantic_search(session, query_vec, top_k * 2, filter_context)
            hyde_results = await self._semantic_search(session, hyde_vec, top_k * 2, filter_context)
            bm25_results = await self._bm25_search(session, query, top_k * 2, filter_context)

        fused = self._reciprocal_rank_fusion(
            [semantic_results, hyde_results, bm25_results],
            k=60,
        )

        return {
            "chunks": fused[:top_k],
            "context": self._format_context(fused[:top_k]),
            "citations": self._extract_citations(fused[:top_k]),
        }

    HYPE_SYSTEM_PROMPT = """You are a search query expansion engine for a government scheme discovery platform.
Generate a detailed hypothetical document passage that would perfectly answer the user's question.
The passage should read like an official government scheme description — factual, specific, with eligibility criteria, benefits, and application details.

Rules:
1. Write a single continuous paragraph (200-300 words)
2. Be specific: include numbers, income limits, age limits, category details
3. Use formal Indian government English
4. Output ONLY the passage, no greetings, no explanations, no meta-commentary
5. If the query is in Hindi or Telugu, write the passage in that language"""

    async def _expand_query(self, query: str) -> str:
        try:
            provider = await ProviderFactory.get_provider_for_use_case("classifier")
            result = await provider.complete(
                messages=[Message(
                    role="user",
                    content=query,
                )],
                system=self.HYPE_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=400,
            )
            expanded = result.content.strip()
            if len(expanded) < 20:
                return query
            logger.info("retriever.hyde_expanded", original_len=len(query), expanded_len=len(expanded))
            return expanded
        except Exception as exc:
            logger.warning("retriever.hyde_failed", error=str(exc))
            return query

    async def _semantic_search(
        self,
        session: AsyncSession,
        query_vec: List[float],
        top_k: int,
        filter_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        vec_str = json.dumps(query_vec)
        params: Dict[str, Any] = {"vec": vec_str, "limit": top_k}
        conditions = ["dc.embedding IS NOT NULL"]

        if filter_context:
            state = filter_context.get("state_code")
            if state and len(state) <= 2 and state.isalpha():
                conditions.append(
                    "(chunk_metadata->>'state_code' = :state OR chunk_metadata->>'state_code' IS NULL)"
                )
                params["state"] = state.upper()

        where_clause = " AND ".join(conditions)
        sql = text(f"""
            SELECT
                dc.id, dc.content, dc.chunk_metadata, dc.document_id,
                dc.scheme_id, dc.token_count,
                1 - (dc.embedding <=> :vec::vector) as similarity
            FROM document_chunks dc
            WHERE {where_clause}
            ORDER BY dc.embedding <=> :vec::vector
            LIMIT :limit
        """)

        result = await session.execute(sql, params)
        rows = result.all()
        return [
            {
                "id": str(r.id),
                "content": r.content,
                "metadata": r.chunk_metadata,
                "document_id": str(r.document_id) if r.document_id else None,
                "scheme_id": str(r.scheme_id) if r.scheme_id else None,
                "token_count": r.token_count,
                "score": float(r.similarity),
                "source": "semantic",
            }
            for r in rows
        ]

    async def _bm25_search(
        self,
        session: AsyncSession,
        query: str,
        top_k: int,
        filter_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        cleaned = " & ".join(query.split()[:10])
        if not cleaned:
            return []

        sql = text(f"""
            SELECT
                dc.id, dc.content, dc.chunk_metadata, dc.document_id,
                dc.scheme_id, dc.token_count,
                ts_rank(to_tsvector('english', dc.content), plainto_tsquery('english', :query)) as rank
            FROM document_chunks dc
            WHERE to_tsvector('english', dc.content) @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """)

        result = await session.execute(sql, {"query": query, "limit": top_k})
        rows = result.all()
        return [
            {
                "id": str(r.id),
                "content": r.content,
                "metadata": r.chunk_metadata,
                "document_id": str(r.document_id) if r.document_id else None,
                "scheme_id": str(r.scheme_id) if r.scheme_id else None,
                "token_count": r.token_count,
                "score": float(r.rank) if r.rank else 0.0,
                "source": "bm25",
            }
            for r in rows
        ]

    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Dict[str, Any]]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        scores: Dict[str, Dict[str, Any]] = {}

        for results in result_lists:
            for rank, item in enumerate(results):
                item_id = item["id"]
                if item_id not in scores:
                    scores[item_id] = {**item, "fusion_score": 0.0}
                scores[item_id]["fusion_score"] += 1.0 / (k + rank + 1)

        fused = sorted(scores.values(), key=lambda x: x["fusion_score"], reverse=True)

        for i, item in enumerate(fused):
            item["rank"] = i + 1
            item["score"] = round(item["fusion_score"], 4)

        return fused

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source_url") or chunk.get("metadata", {}).get("source_url", "unknown")
            parts.append(f"[Source {i}] (relevance: {chunk.get('score', 0):.3f}, from: {source})\n{chunk['content']}")
        return "\n\n".join(parts)

    def _extract_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        seen = set()
        for chunk in chunks:
            scheme_id = chunk.get("scheme_id")
            if scheme_id and scheme_id not in seen:
                seen.add(scheme_id)
                citations.append({
                    "scheme_id": scheme_id,
                    "title": chunk.get("metadata", {}).get("title", ""),
                    "relevance": chunk.get("score", 0),
                    "source_url": chunk.get("metadata", {}).get("source_url"),
                })
        return citations
