from __future__ import annotations

import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

CORRELATION_ID_HEADER = "X-Correlation-ID"
_log_context = structlog.contextvars.bind_contextvars


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER,
            request.headers.get("X-Request-ID", str(uuid.uuid4())),
        )
        _log_context(
            correlation_id=correlation_id,
            method=request.method,
            path=str(request.url.path),
        )

        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
