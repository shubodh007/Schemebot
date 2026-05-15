from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.ai.providers.base import Message
from app.ai.providers.factory import ProviderFactory
from app.ai.rag.embedder import Embedder
from app.ai.rag.reranker import CrossEncoderReranker
from app.ai.rag.retriever import Retriever
from app.core.logging import logger


class RAGPipeline:
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        retriever: Optional[Retriever] = None,
        reranker: Optional[CrossEncoderReranker] = None,
    ) -> None:
        self.embedder = embedder or Embedder()
        self.retriever = retriever or Retriever(embedder=self.embedder)
        self.reranker = reranker or CrossEncoderReranker()

    async def retrieve(
        self,
        query: str,
        top_k: int = 6,
        filter_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        retrieval_result = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            filter_context=filter_context,
        )

        reranked = await self.reranker.rerank(
            query=query,
            candidates=retrieval_result.get("chunks", []),
            top_k=min(3, top_k),
        )

        retrieval_result["chunks"] = reranked
        retrieval_result["context"] = self._format_context(reranked)
        retrieval_result["citations"] = self._extract_citations(reranked)

        return retrieval_result

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source_url", "unknown")
            parts.append(
                f"[Source {i}] (relevance: {chunk.get('rerank_score', chunk.get('score', 0)):.3f}, "
                f"from: {source})\n{chunk['content']}"
            )
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
                    "relevance": chunk.get("rerank_score", chunk.get("score", 0)),
                    "source_url": chunk.get("metadata", {}).get("source_url"),
                })
        return citations
