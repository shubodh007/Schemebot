from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.middleware.correlation_id import CorrelationIDMiddleware
from app.api.middleware.csrf import CSRFMiddleware, CSRFValidationError
from app.api.middleware.error_handler import (
    LoggingMiddleware,
    govscheme_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.middleware.rate_limiter import RateLimitMiddleware
from app.api.middleware.security_headers import SecurityHeadersMiddleware
from app.api.routes import admin, auth, chat, documents, health, legal, password_reset, schemes, search
from app.core.config import settings
from app.core.database import check_database_health
from app.core.exceptions import GovSchemeError
from app.core.logging import logger, setup_logging
from app.core.metrics import metrics_router
from app.core.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(settings.log_level)

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[FastApiIntegration()],
        )
        logger.info("sentry.initialized")

    try:
        await redis_client.initialize()
    except Exception as exc:
        logger.warning("redis.initialization_failed", error=str(exc))

    db_healthy = await check_database_health()
    if not db_healthy:
        logger.warning("database.initial_health_check_failed")
    else:
        logger.info("database.healthy")

    logger.info(
        "app.startup",
        environment=settings.environment.value,
        api_prefix=settings.api_v1_prefix,
    )

    yield

    await redis_client.close()
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="GovScheme AI API",
        description="AI-powered civic platform for Indian government welfare scheme discovery",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Limit"],
    )

    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFMiddleware, secret_key=settings.secret_key)

    app.add_exception_handler(GovSchemeError, govscheme_exception_handler)
    app.add_exception_handler(CSRFValidationError, govscheme_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    from fastapi.exceptions import RequestValidationError
    from app.api.middleware.error_handler import validation_exception_handler
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    prefix = settings.api_v1_prefix

    app.include_router(health.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(password_reset.router, prefix=prefix)
    app.include_router(schemes.router, prefix=prefix)
    app.include_router(chat.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(legal.router, prefix=prefix)
    app.include_router(search.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)
    app.include_router(metrics_router, prefix=prefix)

    @app.get("/")
    async def root():
        return {"name": "GovScheme AI", "version": "0.1.0", "status": "running"}

    return app


app = create_app()
