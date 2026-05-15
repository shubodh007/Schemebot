from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import EligibilityEngineError, NotFoundError
from app.core.logging import logger
from app.models.scheme import EligibilityOp, Scheme
from app.repositories.scheme_repo import (
    SavedSchemeRepository,
    SchemeCategoryRepository,
    SchemeRepository,
)
from app.schemas.scheme import EligibilityMatch, ProfileOverride


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

        matches: List[EligibilityMatch] = []
        for scheme in all_schemes:
            result = self._evaluate_scheme_rules(scheme, merged)
            matches.append(result)

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

    def _evaluate_scheme_rules(
        self, scheme: Scheme, profile: Dict[str, Any]
    ) -> EligibilityMatch:
        matching_rules: List[str] = []
        failing_rules: List[str] = []
        missing_fields: List[str] = []
        total_rules = len(scheme.eligibility_rules)

        if total_rules == 0:
            return EligibilityMatch(
                scheme=scheme,
                score=0.5,
                eligible=False,
                matching_rules=["No eligibility rules defined for this scheme"],
                failing_rules=[],
                missing_fields=[],
            )

        passed = 0
        for rule in scheme.eligibility_rules:
            user_value = profile.get(rule.field_name)
            if user_value is None:
                if rule.is_mandatory:
                    failing_rules.append(
                        f"{rule.field_name}: missing information"
                    )
                    missing_fields.append(rule.field_name)
                else:
                    matching_rules.append(
                        f"{rule.field_name}: optional rule, skipped (no data)"
                    )
                    passed += 1
                continue

            rule_value = rule.value
            if isinstance(rule_value, str):
                try:
                    rule_value = __import__("json").loads(rule_value)
                except (__import__("json").JSONDecodeError, TypeError):
                    pass

            passed_rule = self._evaluate_rule(rule.field_name, rule.operator, user_value, rule_value)

            if passed_rule:
                matching_rules.append(
                    f"{rule.field_name}: {user_value} {rule.operator.value} {rule_value}"
                )
                if rule.is_mandatory or True:
                    passed += 1
            else:
                failing_rules.append(
                    f"{rule.field_name}: {user_value} does not satisfy {rule.operator.value} {rule_value}"
                )

        score = passed / max(total_rules, 1) if total_rules > 0 else 0
        mandatory_failures = [
            r for r, ru in zip(scheme.eligibility_rules, matching_rules + failing_rules)
            if ru in failing_rules and r.is_mandatory
        ]
        eligible = len(mandatory_failures) == 0 and score >= 0.3

        return EligibilityMatch(
            scheme=scheme,
            score=round(score, 4),
            eligible=eligible,
            matching_rules=matching_rules,
            failing_rules=failing_rules,
            missing_fields=missing_fields,
        )

    def _evaluate_rule(
        self, field_name: str, operator: EligibilityOp, user_value: Any, rule_value: Any
    ) -> bool:
        try:
            if isinstance(rule_value, dict):
                if "min" in rule_value and "max" in rule_value:
                    lower = rule_value["min"]
                    upper = rule_value["max"]
                    return lower <= user_value <= upper
                if "values" in rule_value:
                    rule_value = rule_value["values"]

            if isinstance(user_value, str) and isinstance(rule_value, str):
                user_value = user_value.lower()
                rule_value = rule_value.lower()

            if operator == EligibilityOp.EQ:
                return str(user_value).lower() == str(rule_value).lower()
            elif operator == EligibilityOp.NEQ:
                return str(user_value).lower() != str(rule_value).lower()
            elif operator == EligibilityOp.LT:
                return float(user_value) < float(rule_value)
            elif operator == EligibilityOp.LTE:
                return float(user_value) <= float(rule_value)
            elif operator == EligibilityOp.GT:
                return float(user_value) > float(rule_value)
            elif operator == EligibilityOp.GTE:
                return float(user_value) >= float(rule_value)
            elif operator == EligibilityOp.IN:
                values = rule_value if isinstance(rule_value, list) else [rule_value]
                return str(user_value).lower() in [str(v).lower() for v in values]
            elif operator == EligibilityOp.NOT_IN:
                values = rule_value if isinstance(rule_value, list) else [rule_value]
                return str(user_value).lower() not in [str(v).lower() for v in values]
            elif operator == EligibilityOp.BETWEEN:
                if isinstance(rule_value, list) and len(rule_value) == 2:
                    return float(rule_value[0]) <= float(user_value) <= float(rule_value[1])
                return False
            elif operator == EligibilityOp.CONTAINS:
                return str(rule_value).lower() in str(user_value).lower()
            else:
                logger.warning("eligibility.unknown_operator", operator=str(operator))
                return False
        except (ValueError, TypeError, ZeroDivisionError) as exc:
            logger.warning(
                "eligibility.rule_evaluation_failed",
                field=field_name,
                op=str(operator),
                error=str(exc),
            )
            return False

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
