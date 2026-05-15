from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.middleware.auth_middleware import current_user, require_admin
from app.core.database import get_session
from app.core.logging import logger
from app.models.user import User, UserStatus
from app.models.scheme import Scheme, SchemeStatus
from app.models.conversation import Conversation, Message
from app.models.scraping import ScrapingJob
from app.repositories.user_repo import UserRepository
from app.repositories.scheme_repo import SchemeRepository

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    conditions = []
    if status:
        conditions.append(User.status == UserStatus(status))
    skip = (page - 1) * limit
    users, total = await repo.get_many(*conditions, skip=skip, limit=limit)
    return {"users": users, "total": total, "page": page, "has_more": (skip + limit) < total}


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    body: dict,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    allowed = {"role", "status"}
    update_data = {k: v for k, v in body.items() if k in allowed}
    updated = await repo.update(user_id, **update_data)
    if updated is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User not found")
    return {"user": updated}


@router.get("/analytics")
async def get_analytics(
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user_count = await session.scalar(select(func.count(User.id)))
    scheme_count = await session.scalar(select(func.count(Scheme.id)).where(Scheme.status == SchemeStatus.ACTIVE))
    conv_count = await session.scalar(select(func.count(Conversation.id)))
    msg_count = await session.scalar(select(func.count(Message.id)))

    return {
        "users": user_count or 0,
        "active_schemes": scheme_count or 0,
        "conversations": conv_count or 0,
        "messages": msg_count or 0,
        "ai_providers_used": ["openrouter"],
    }


@router.get("/scraping/jobs")
async def list_scraping_jobs(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(ScrapingJob).order_by(ScrapingJob.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(stmt)
    jobs = list(result.scalars().all())
    return {"jobs": jobs, "total": len(jobs), "page": page}


@router.post("/scraping/trigger")
async def trigger_scrape(
    body: dict,
    user: User = Depends(require_admin),
):
    source = body.get("source", "myscheme")
    from app.scraper.engine import ScrapingEngine
    from app.models.scraping import ScrapingJob
    from app.core.database import async_session_factory

    engine = ScrapingEngine()

    async with async_session_factory() as session:
        job = ScrapingJob(
            source_name=source,
            source_url=engine.sources.get(source, {}).get("url", ""),
            job_type="on_demand",
            status="running",
            triggered_by=user.id,
        )
        session.add(job)
        await session.flush()

        try:
            found, created, updated = await engine.scrape_source(source, job)
            job.status = "completed"
            job.schemes_found = found
            job.schemes_new = created
            job.schemes_updated = updated
            job.finished_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)

        await session.commit()

    return {"job_id": str(job.id), "status": job.status, "schemes_found": job.schemes_found}
