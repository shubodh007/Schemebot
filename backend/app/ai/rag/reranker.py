from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import logger


class CrossEncoderReranker:
    _model = None
    _load_lock: asyncio.Lock | None = None

    def __init__(self) -> None:
        if CrossEncoderReranker._load_lock is None:
            CrossEncoderReranker._load_lock = asyncio.Lock()

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        if CrossEncoderReranker._model is None:
            async with CrossEncoderReranker._load_lock:
                if CrossEncoderReranker._model is None:
                    await self._load_model()

        if CrossEncoderReranker._model is None:
            return candidates[:top_k]

        pairs = [(query, c["content"]) for c in candidates]

        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            CrossEncoderReranker._model.predict,
            pairs,
        )

        if isinstance(scores[0], list):
            scores = [s[1] for s in scores]

        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for i, (candidate, score) in enumerate(scored[:top_k]):
            candidate["rerank_score"] = float(score)
            candidate["rank"] = i + 1
            results.append(candidate)

        return results

    async def _load_model(self) -> None:
        try:
            from sentence_transformers import CrossEncoder
            CrossEncoderReranker._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            CrossEncoderReranker._model.model.eval()
            logger.info("reranker.model_loaded", model="cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as exc:
            logger.error("reranker.model_load_failed", error=str(exc))
        finally:
            CrossEncoderReranker._load_lock = False
