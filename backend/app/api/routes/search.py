from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth_middleware import current_user, optional_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.document import SearchResult, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str,
    type: Optional[str] = "all",
    language: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    user: Optional[User] = Depends(optional_user),
    session: AsyncSession = Depends(get_session),
):
    from app.repositories.scheme_repo import SchemeRepository
    from app.models.scheme import Scheme
    from sqlalchemy import or_, select

    repo = SchemeRepository(session)
    search_pattern = f"%{q}%"

    stmt = (
        select(Scheme)
        .where(
            or_(
                Scheme.title.ilike(search_pattern),
                Scheme.description.ilike(search_pattern),
                Scheme.title_hi.ilike(search_pattern),
                Scheme.title_te.ilike(search_pattern),
                Scheme.tags.any(q),
            )
        )
        .where(Scheme.status == "active")
        .order_by(Scheme.beneficiaries_count.desc().nullslast())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await session.execute(stmt)
    schemes = list(result.scalars().all())

    count_stmt = select(__import__("sqlalchemy").func.count()).select_from(Scheme).where(
        or_(
            Scheme.title.ilike(search_pattern),
            Scheme.description.ilike(search_pattern),
            Scheme.title_hi.ilike(search_pattern),
            Scheme.title_te.ilike(search_pattern),
        )
    )
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    search_results = []
    for s in schemes:
        search_results.append(SearchResult(
            id=s.id,
            title=s.title,
            title_hi=s.title_hi,
            title_te=s.title_te,
            description=s.description[:200] + "..." if len(s.description) > 200 else s.description,
            type="scheme",
            score=0.8,
            url=f"/schemes/{s.slug}",
            metadata={"level": s.level.value, "state_code": s.state_code, "status": s.status.value},
        ))

    return SearchResponse(
        results=search_results,
        suggestions=[],
        elapsed_ms=0,
        total=total,
    )


@router.get("/suggestions")
async def suggestions(
    q: str,
):
    if not q or len(q) < 2:
        return {"suggestions": []}
    return {"suggestions": [f"{q} scheme", f"{q} eligibility", f"{q} benefit"]}
