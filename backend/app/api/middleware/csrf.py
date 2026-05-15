from __future__ import annotations

import hmac
import secrets
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.exceptions import GovSchemeError
from app.core.logging import logger

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"


class CSRFValidationError(GovSchemeError):
    status_code = 403
    code = "CSRF_VALIDATION_FAILED"
    detail = "CSRF validation failed"


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, secret_key: str = "") -> None:
        super().__init__(app)
        self._secret = secret_key or "csrf-secret-change-in-production"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in SAFE_METHODS:
            cookie_token = request.cookies.get(CSRF_COOKIE)
            header_token = request.headers.get(CSRF_HEADER)

            if not cookie_token or not header_token:
                logger.warning(
                    "csrf.missing_tokens",
                    method=request.method,
                    path=str(request.url.path),
                    has_cookie=cookie_token is not None,
                    has_header=header_token is not None,
                )
                raise CSRFValidationError("CSRF token missing")

            if not hmac.compare_digest(cookie_token, header_token):
                logger.warning(
                    "csrf.token_mismatch",
                    method=request.method,
                    path=str(request.url.path),
                )
                raise CSRFValidationError("CSRF token mismatch")

        response = await call_next(request)

        if request.method in SAFE_METHODS:
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                key=CSRF_COOKIE,
                value=token,
                httponly=False,
                samesite="strict",
                secure=True,
                max_age=86400,
                path="/",
            )

        return response
