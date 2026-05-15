from __future__ import annotations

from typing import Any, Dict, Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import GovSchemeError, ValidationError
from app.core.logging import logger


async def govscheme_exception_handler(request: Request, exc: GovSchemeError) -> JSONResponse:
    logger.error(
        "api.error",
        path=str(request.url.path),
        method=request.method,
        code=exc.code,
        detail=exc.detail,
        metadata=exc.metadata,
    )

    response_body: Dict[str, Any] = {
        "code": exc.code,
        "detail": exc.detail,
    }
    if isinstance(exc, ValidationError) and hasattr(exc, "errors"):
        response_body["errors"] = exc.errors
    if exc.metadata:
        response_body["metadata"] = exc.metadata

    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for err in exc.errors():
        errors.append({
            "loc": err.get("loc", []),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        })

    logger.warning(
        "api.validation_error",
        path=str(request.url.path),
        errors=errors,
    )

    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "api.unhandled_error",
        path=str(request.url.path),
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "detail": "An unexpected error occurred. Our team has been notified.",
        },
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any):
        start = __import__("time").time()
        response = await call_next(request)
        elapsed = int((__import__("time").time() - start) * 1000)

        if elapsed > 1000:
            logger.warning(
                "api.slow_request",
                path=str(request.url.path),
                method=request.method,
                elapsed_ms=elapsed,
                status=response.status_code,
            )

        return response
