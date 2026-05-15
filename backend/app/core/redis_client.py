from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import orjson
from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.client import Pipeline

from app.core.config import settings
from app.core.logging import logger


class RedisClient:
    def __init__(self) -> None:
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None

    async def initialize(self) -> None:
        self._pool = ConnectionPool.from_url(
            settings.upstash_redis_url,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        self._client = Redis.from_pool(self._pool)
        await self._client.ping()
        logger.info("redis.connected", url=settings.upstash_redis_url.split("@")[-1] if "@" in settings.upstash_redis_url else "local")

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.aclose()
        logger.info("redis.disconnected")

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._client

    # ── Generic Cache ──────────────────────────────────────────

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def get_json(self, key: str) -> Optional[Any]:
        value = await self.client.get(key)
        if value is None:
            return None
        return orjson.loads(value)

    async def set(
        self, key: str, value: str, ttl: Optional[int] = None
    ) -> None:
        if ttl is not None:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)

    async def set_json(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        serialized = orjson.dumps(value, default=str)
        if ttl is not None:
            await self.client.setex(key, ttl, serialized)
        else:
            await self.client.set(key, serialized)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    async def expire(self, key: str, ttl: int) -> None:
        await self.client.expire(key, ttl)

    # ── Rate Limiting (Sliding Window) ─────────────────────────

    async def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> Tuple[bool, int]:
        now = __import__("time").time()
        window_start = now - window_seconds

        pipe: Pipeline = self.client.pipeline()
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)

        _, count, _, _ = await pipe.execute()

        allowed = count <= max_requests
        remaining = max(0, max_requests - count)
        return allowed, int(remaining)

    # ── Cache with TTL ─────────────────────────────────────────

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: int = 300,
    ) -> Any:
        cached = await self.get_json(key)
        if cached is not None:
            return cached
        value = await factory() if callable(factory) else factory
        await self.set_json(key, value, ttl)
        return value

    # ── Session Store ──────────────────────────────────────────

    async def store_session(
        self, session_id: str, data: Dict[str, Any], ttl: int = 86400
    ) -> None:
        await self.set_json(f"session:{session_id}", data, ttl)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await self.get_json(f"session:{session_id}")

    async def delete_session(self, session_id: str) -> None:
        await self.delete(f"session:{session_id}")

    # ── Cache Invalidation Patterns ────────────────────────────

    async def invalidate_pattern(self, pattern: str) -> int:
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self.client.scan(
                cursor=cursor, match=pattern, count=100
            )
            if keys:
                await self.client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        return deleted


redis_client = RedisClient()
