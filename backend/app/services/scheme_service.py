from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EligibilityEngineError, NotFoundError
from app.core.logging import logger
from app.models.scheme import Scheme
from app.repositories.scheme_repo import (
    SavedSchemeRepository,
    SchemeCategoryRepository,
    SchemeRepository,
)
from app.schemas.scheme import EligibilityMatch, ProfileOverride
from app.services.eligibility_evaluator import EligibilityEvaluator


class SchemeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.scheme_repo = SchemeRepository(session)
        self.category_repo = SchemeCategoryRepository(session)
        self.saved_repo = SavedSchemeRepository(session)

    async def get_scheme(self, scheme_id: UUID) -> Scheme:
        scheme = await self.scheme_repo.get_with_rules(scheme_id)
        if scheme is None:
            raise NotFoundError(f"Scheme {scheme_id} not found")
        return scheme

    async def get_scheme_by_slug(self, slug: str) -> Scheme:
        scheme = await self.scheme_repo.get_by_slug(slug)
        if scheme is None:
            raise NotFoundError(f"Scheme '{slug}' not found")
        return scheme

    async def search_schemes(
        self,
        query: str = "",
        category_id: Optional[UUID] = None,
        level: Optional[str] = None,
        state_code: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        skip = (page - 1) * limit
        items, total = await self.scheme_repo.search(
            query=query,
            category_id=category_id,
            level=level,
            state_code=state_code,
            skip=skip,
            limit=limit,
        )
        return {
            "schemes": items,
            "total": total,
            "page": page,
            "has_more": (skip + limit) < total,
        }

    async def get_categories(self) -> List[Dict[str, Any]]:
        return await self.category_repo.get_all_with_counts()

    async def check_eligibility(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        profile_override: Optional[ProfileOverride] = None,
    ) -> Dict[str, Any]:
        if profile_override:
            merged = {**profile_data, **profile_override.model_dump(exclude_none=True)}
        else:
            merged = profile_data

        logger.info("eligibility.check.started", user_id=str(user_id))

        all_schemes = await self.scheme_repo.get_matching_schemes(merged)
        evaluator = EligibilityEvaluator()

        eval_results = await asyncio.gather(*[
            evaluator.evaluate(scheme, merged) for scheme in all_schemes
        ])

        matches: List[EligibilityMatch] = []
        for eval_result, scheme in zip(eval_results, all_schemes):
            matches.append(EligibilityMatch(
                scheme=scheme,
                score=eval_result.score,
                eligible=eval_result.eligible,
                matching_rules=[r.reason for r in eval_result.rule_results if r.passed],
                failing_rules=[r.reason for r in eval_result.rule_results if not r.passed],
                missing_fields=eval_result.missing_fields,
            ))

        matches.sort(key=lambda m: m.score, reverse=True)

        filled_fields = sum(1 for v in merged.values() if v is not None)
        total_fields = len([
            k for k in [
                "annual_income", "caste_category", "state_code", "gender",
                "disability_status", "is_farmer", "is_bpl", "education_level",
            ]
        ])
        completeness = filled_fields / max(total_fields, 1)

        logger.info(
            "eligibility.check.completed",
            user_id=str(user_id),
            matches_found=sum(1 for m in matches if m.eligible),
        )

        return {
            "matches": matches,
            "checked_at": datetime.now(timezone.utc),
            "profile_completeness": completeness,
        }

    async def save_scheme(
        self, user_id: UUID, scheme_id: UUID, notes: Optional[str] = None
    ) -> None:
        scheme = await self.scheme_repo.get_by_id(scheme_id)
        if scheme is None:
            raise NotFoundError(f"Scheme {scheme_id} not found")
        await self.saved_repo.create(user_id=user_id, scheme_id=scheme_id, notes=notes)

    async def unsave_scheme(self, user_id: UUID, scheme_id: UUID) -> None:
        deleted = await self.saved_repo.delete_by_user_and_scheme(user_id, scheme_id)
        if not deleted:
            raise NotFoundError(f"Saved scheme {scheme_id} not found for this user")

    async def get_saved_schemes(self, user_id: UUID) -> List[Any]:
        return await self.saved_repo.get_user_saved(user_id)
