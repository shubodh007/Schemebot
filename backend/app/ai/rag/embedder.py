from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import logger


class Embedder:
    def __init__(self) -> None:
        self.model = settings.google_embedding_model
        self.api_key = settings.google_ai_api_key
        self._local_model = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.api_key:
            return await self._embed_google(texts)

        return await self._embed_local(texts)

    async def _embed_google(self, texts: List[str]) -> List[List[float]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            results = []
            for text in texts:
                response = await client.post(
                    url,
                    json={"model": f"models/{self.model}", "content": {"parts": [{"text": text}]}},
                )
                if response.status_code != 200:
                    logger.error("embedder.google.error", status=response.status_code, body=response.text[:300])
                    raise RuntimeError(f"Google embedding error: {response.status_code}")
                data = response.json()
                embedding = data.get("embedding", {}).get("values", [])
                results.append(embedding)
            return results

    async def _embed_local(self, texts: List[str]) -> List[List[float]]:
        if self._local_model is None:
            self._local_model = await self._load_local_model()

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            self._local_model.encode,
            texts,
        )
        return embeddings.tolist()

    async def _load_local_model(self) -> Any:
        from sentence_transformers import SentenceTransformer
        logger.info("embedder.loading_local_model", model="BAAI/bge-small-en-v1.5")
        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        model.eval()
        return model

    async def embed_query(self, text: str) -> List[float]:
        embeddings = await self.embed([text])
        return embeddings[0] if embeddings else []
