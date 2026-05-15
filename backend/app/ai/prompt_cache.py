from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from app.ai.providers.base import Message, CompletionResult
from app.core.logging import logger
from app.core.redis_client import RedisClient


class PromptCache:
    def __init__(self, redis: RedisClient, ttl: int = 3600) -> None:
        self._redis = redis
        self._ttl = ttl

    def _key(self, model: str, system: Optional[str], messages: List[Message], temperature: float, use_case: str) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "system": system,
            "messages": [{"role": m.role, "content": m.content} for m in messages[-5:]],
            "temperature": round(temperature, 1),
            "use_case": use_case,
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        return f"prompt:{digest}"

    async def get(self, model: str, system: Optional[str], messages: List[Message], temperature: float, use_case: str) -> Optional[CompletionResult]:
        if temperature > 0.0:
            return None
        key = self._key(model, system, messages, temperature, use_case)
        cached = await self._redis.get_json(key)
        if cached:
            logger.info("prompt_cache.hit", use_case=use_case, model=model)
            return CompletionResult(**cached)
        return None

    async def set(self, model: str, system: Optional[str], messages: List[Message], temperature: float, use_case: str, result: CompletionResult) -> None:
        if temperature > 0.0:
            return
        key = self._key(model, system, messages, temperature, use_case)
        await self._redis.set_json(key, {
            "content": result.content,
            "model": result.model,
            "provider": result.provider,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "latency_ms": result.latency_ms,
            "metadata": result.metadata,
        }, ttl=self._ttl)
        logger.info("prompt_cache.set", use_case=use_case, model=model)
