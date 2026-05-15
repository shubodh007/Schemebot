from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth_middleware import current_user, optional_user
from app.core.database import get_session
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.scheme_repo import SavedSchemeRepository
from app.repositories.user_repo import ProfileRepository
from app.schemas.scheme import (
    CompareSchemesRequest,
    ComparisonResult,
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    SaveSchemeRequest,
    SavedSchemeResponse,
    SchemeDetail,
    SchemeDetailWithEligibility,
    SchemeEligibilityResponse,
    SchemeListResponse,
)
from app.services.scheme_service import SchemeService

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("")
async def list_schemes(
    query: str = "",
    category_id: Optional[str] = None,
    level: Optional[str] = None,
    state_code: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    cat_uuid = UUID(category_id) if category_id else None
    result = await service.search_schemes(
        query=query,
        category_id=cat_uuid,
        level=level,
        state_code=state_code,
        page=page,
        limit=limit,
    )
    return result


@router.get("/categories")
async def list_categories(
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    return await service.get_categories()


@router.get("/{scheme_id}")
async def get_scheme(
    scheme_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    scheme = await service.get_scheme(scheme_id)
    return {"scheme": SchemeDetailWithEligibility.model_validate(scheme)}


@router.post("/eligibility-check")
async def check_eligibility(
    body: EligibilityCheckRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    profile_repo = ProfileRepository(session)
    profile = await profile_repo.get_by_user_id(user.id)

    profile_data = {
        "annual_income": float(profile.annual_income) if profile and profile.annual_income else None,
        "caste_category": profile.caste_category.value if profile and profile.caste_category else None,
        "state_code": profile.state_code if profile else None,
        "gender": profile.gender.value if profile and profile.gender else None,
        "disability_status": profile.disability_status.value if profile else "none",
        "is_farmer": profile.is_farmer if profile else False,
        "is_bpl": profile.is_bpl if profile else False,
        "education_level": profile.education_level if profile else None,
        "date_of_birth": str(profile.date_of_birth) if profile and profile.date_of_birth else None,
    }

    result = await service.check_eligibility(
        user_id=user.id,
        profile_data=profile_data,
        profile_override=body.profile_override,
    )
    return result


@router.get("/{scheme_id}/eligibility")
async def get_scheme_eligibility(
    scheme_id: UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    profile_repo = ProfileRepository(session)
    profile = await profile_repo.get_by_user_id(user.id)

    profile_data = {
        "annual_income": float(profile.annual_income) if profile and profile.annual_income else None,
        "caste_category": profile.caste_category.value if profile and profile.caste_category else None,
        "state_code": profile.state_code if profile else None,
        "gender": profile.gender.value if profile and profile.gender else None,
        "disability_status": profile.disability_status.value if profile else "none",
        "is_farmer": profile.is_farmer if profile else False,
        "is_bpl": profile.is_bpl if profile else False,
        "education_level": profile.education_level if profile else None,
    }

    result = await service.check_eligibility(user_id=user.id, profile_data=profile_data)

    for match in result["matches"]:
        if str(match.scheme.id) == str(scheme_id):
            return SchemeEligibilityResponse(
                eligible=match.eligible,
                score=match.score,
                reasons=match.matching_rules + match.failing_rules,
                missing_fields=match.missing_fields,
            )

    from app.core.exceptions import NotFoundError
    raise NotFoundError(f"Scheme {scheme_id} not found in eligibility results")


@router.post("/{scheme_id}/save")
async def save_scheme(
    scheme_id: UUID,
    body: SaveSchemeRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    await service.save_scheme(
        user_id=user.id,
        scheme_id=scheme_id,
        notes=body.notes,
    )
    return {"detail": "Scheme saved"}


@router.delete("/{scheme_id}/save")
async def unsave_scheme(
    scheme_id: UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    await service.unsave_scheme(user_id=user.id, scheme_id=scheme_id)
    return None


@router.get("/saved/list")
async def get_saved_schemes(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    saved = await service.get_saved_schemes(user.id)
    return {"saved": [SavedSchemeResponse.model_validate(s) for s in saved]}


@router.post("/compare")
async def compare_schemes(
    body: CompareSchemesRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SchemeService(session)
    schemes = []
    for sid in body.scheme_ids:
        scheme = await service.get_scheme(sid)
        schemes.append(scheme)

    return {
        "id": None,
        "name": body.name,
        "schemes": [SchemeDetail.model_validate(s) for s in schemes],
        "comparison_fields": [
            "eligibility_rules", "benefits", "level", "ministry",
            "application_url", "status",
        ],
        "created_at": None,
    }
