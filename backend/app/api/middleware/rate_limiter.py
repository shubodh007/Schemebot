from __future__ import annotations

import ipaddress
import time
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.exceptions import RateLimitError
from app.core.logging import logger
from app.core.redis_client import redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if path.startswith("/health"):
            return await call_next(request)

        ip = self._get_client_ip(request)
        route_key = self._get_route_key(path)
        user_id = getattr(request.state, "user_id", None)

        if user_id:
            limit_key = f"ratelimit:{route_key}:user:{user_id}"
            max_req = self._get_max_requests(route_key)
        else:
            limit_key = f"ratelimit:{route_key}:ip:{ip}"
            max_req = min(
                self._get_max_requests(route_key),
                settings.rate_limit_default_max,
            )

        try:
            allowed, remaining = await redis_client.check_rate_limit(
                limit_key,
                max_req,
                settings.rate_limit_window_seconds,
            )
        except Exception:
            allowed, remaining = True, max_req

        if not allowed:
            raise RateLimitError()

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        client = request.client
        return client.host if client else "unknown"

    def _get_route_key(self, path: str) -> str:
        if "/auth/" in path:
            return "auth"
        if "/chat/" in path:
            return "chat"
        if "/documents/" in path:
            return "documents"
        if "/admin/" in path:
            return "admin"
        if "/search" in path:
            return "search"
        return "default"

    def _get_max_requests(self, route_key: str) -> int:
        limits = {
            "auth": settings.rate_limit_auth_max,
            "chat": settings.rate_limit_chat_max,
            "documents": 10,
            "admin": 30,
            "search": 30,
            "default": settings.rate_limit_default_max,
        }
        return limits.get(route_key, limits["default"])
