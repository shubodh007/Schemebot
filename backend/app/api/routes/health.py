from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.database import check_database_health
from app.core.logging import logger

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    db_healthy = await check_database_health()
    if not db_healthy:
        from fastapi import Response
        return Response(status_code=503, content='{"status":"unhealthy","database":"disconnected"}')
    return {"status": "ok", "database": "connected"}


@router.get("/health/version")
async def version():
    return {
        "version": "0.1.0",
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "environment": __import__("app.core.config", fromlist=["settings"]).settings.environment.value,
    }
