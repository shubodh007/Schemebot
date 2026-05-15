from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.logging import logger
from app.models.scheme import EligibilityOp, Scheme, SchemeEligibilityRule


@dataclass
class RuleResult:
    field_name: str
    passed: bool
    reason: str
    is_mandatory: bool


@dataclass
class EligibilityResult:
    scheme_id: UUID
    scheme_title: str
    score: float
    eligible: bool
    rule_results: List[RuleResult] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)


class EligibilityEvaluator:
    def __init__(self) -> None:
        pass

    async def evaluate(
        self,
        scheme: Scheme,
        profile: Dict[str, Any],
    ) -> EligibilityResult:
        rules = scheme.eligibility_rules
        if not rules:
            return EligibilityResult(
                scheme_id=scheme.id,
                scheme_title=scheme.title,
                score=0.5,
                eligible=False,
                rule_results=[RuleResult("_no_rules", False, "No eligibility rules defined", False)],
            )

        rule_results: List[RuleResult] = []
        missing: List[str] = []

        for rule in rules:
            result = self._evaluate_single_rule(rule, profile)
            if result is None:
                missing.append(rule.field_name)
                rule_results.append(
                    RuleResult(
                        field_name=rule.field_name,
                        passed=not rule.is_mandatory,
                        reason=f"Missing field: {rule.field_name}",
                        is_mandatory=rule.is_mandatory,
                    )
                )
            else:
                rule_results.append(result)

        passed = sum(1 for r in rule_results if r.passed)
        total = max(len(rule_results), 1)
        score = passed / total

        mandatory_failures = [r for r in rule_results if not r.passed and r.is_mandatory]
        eligible = len(mandatory_failures) == 0 and score >= 0.3

        return EligibilityResult(
            scheme_id=scheme.id,
            scheme_title=scheme.title,
            score=round(score, 4),
            eligible=eligible,
            rule_results=rule_results,
            missing_fields=missing,
        )

    def _evaluate_single_rule(
        self,
        rule: SchemeEligibilityRule,
        profile: Dict[str, Any],
    ) -> Optional[RuleResult]:
        user_value = profile.get(rule.field_name)
        if user_value is None:
            return None

        rule_value = rule.value
        if isinstance(rule_value, str):
            try:
                import json
                rule_value = json.loads(rule_value)
            except (json.JSONDecodeError, TypeError):
                pass

        passed = self._evaluate_operator(
            field_name=rule.field_name,
            operator=rule.operator,
            user_value=user_value,
            rule_value=rule_value,
        )

        return RuleResult(
            field_name=rule.field_name,
            passed=passed,
            reason=f"{rule.field_name}: {user_value} {'matches' if passed else 'does not match'} {rule.operator.value} {rule_value}",
            is_mandatory=rule.is_mandatory,
        )

    def _evaluate_operator(
        self,
        field_name: str,
        operator: EligibilityOp,
        user_value: Any,
        rule_value: Any,
    ) -> bool:
        try:
            if isinstance(rule_value, dict):
                if "min" in rule_value and "max" in rule_value:
                    return float(rule_value["min"]) <= float(user_value) <= float(rule_value["max"])
                if "values" in rule_value:
                    rule_value = rule_value["values"]

            match operator:
                case EligibilityOp.EQ:
                    return str(user_value).lower() == str(rule_value).lower()
                case EligibilityOp.NEQ:
                    return str(user_value).lower() != str(rule_value).lower()
                case EligibilityOp.LT:
                    return float(user_value) < float(rule_value)
                case EligibilityOp.LTE:
                    return float(user_value) <= float(rule_value)
                case EligibilityOp.GT:
                    return float(user_value) > float(rule_value)
                case EligibilityOp.GTE:
                    return float(user_value) >= float(rule_value)
                case EligibilityOp.IN:
                    values = rule_value if isinstance(rule_value, list) else [rule_value]
                    return str(user_value).lower() in [str(v).lower() for v in values]
                case EligibilityOp.NOT_IN:
                    values = rule_value if isinstance(rule_value, list) else [rule_value]
                    return str(user_value).lower() not in [str(v).lower() for v in values]
                case EligibilityOp.BETWEEN:
                    if isinstance(rule_value, list) and len(rule_value) == 2:
                        return float(rule_value[0]) <= float(user_value) <= float(rule_value[1])
                    return False
                case EligibilityOp.CONTAINS:
                    return str(rule_value).lower() in str(user_value).lower()
                case _:
                    logger.warning("eligibility.unknown_operator", operator=str(operator))
                    return False

        except (ValueError, TypeError, ZeroDivisionError) as exc:
            logger.warning("eligibility.evaluation_failed", field=field_name, op=str(operator), error=str(exc))
            return False
