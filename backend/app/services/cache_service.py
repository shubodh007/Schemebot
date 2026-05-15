from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, TypeVar
from uuid import UUID

from app.core.logging import logger
from app.core.redis_client import RedisClient

T = TypeVar("T")


class ResponseCache:
    def __init__(self, redis: RedisClient, prefix: str = "cache", ttl: int = 300) -> None:
        self._redis = redis
        self._prefix = prefix
        self._ttl = ttl

    def _key(self, parts: List[str]) -> str:
        raw = ":".join(parts)
        digest = hashlib.md5(raw.encode()).hexdigest()
        return f"{self._prefix}:{digest}"

    async def get(self, key_parts: List[str]) -> Optional[Any]:
        key = self._key(key_parts)
        cached = await self._redis.get_json(key)
        if cached is not None:
            logger.debug("cache.hit", key=key)
        return cached

    async def set(self, key_parts: List[str], value: Any) -> None:
        key = self._key(key_parts)
        await self._redis.set_json(key, value, ttl=self._ttl)

    async def invalidate_pattern(self, pattern: str) -> int:
        return await self._redis.invalidate_pattern(f"{self._prefix}:{pattern}*")

    async def invalidate_all(self) -> None:
        await self._redis.invalidate_pattern(f"{self._prefix}:*")


class SchemeListCache(ResponseCache):
    def __init__(self, redis: RedisClient) -> None:
        super().__init__(redis, prefix="scheme_list", ttl=300)

    async def get_list(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        parts = [f"{k}:{v}" for k, v in sorted(params.items()) if v is not None]
        return await self.get(parts)

    async def set_list(self, params: Dict[str, Any], result: Dict[str, Any]) -> None:
        parts = [f"{k}:{v}" for k, v in sorted(params.items()) if v is not None]
        await self.set(parts, result)

    async def invalidate_category(self, category_id: UUID) -> None:
        await self._redis.invalidate_pattern(f"{self._prefix}:*cat:{category_id}*")
