from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models.scheme import EligibilityOp, Scheme, SchemeEligibilityRule
from app.services.eligibility_evaluator import EligibilityEvaluator


def _make_scheme(rules: list[SchemeEligibilityRule]) -> Scheme:
    scheme = Scheme(
        id=uuid.uuid4(),
        title="Test Scheme",
        description="A test scheme",
        slug="test-scheme",
        level="central",
        status="active",
        source_url="https://example.com",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    scheme.eligibility_rules = rules
    return scheme


def _rule(field: str, op: EligibilityOp, value: object, mandatory: bool = True) -> SchemeEligibilityRule:
    return SchemeEligibilityRule(
        id=uuid.uuid4(),
        scheme_id=uuid.uuid4(),
        field_name=field,
        operator=op,
        value=value,
        is_mandatory=mandatory,
    )


class TestEligibilityEvaluator:
    @pytest.mark.asyncio
    async def test_all_rules_pass(self):
        scheme = _make_scheme([
            _rule("annual_income", EligibilityOp.LTE, 300000),
            _rule("age", EligibilityOp.GTE, 18),
        ])
        result = await EligibilityEvaluator().evaluate(scheme, {"annual_income": 200000, "age": 30})
        assert result.eligible is True
        assert result.score >= 0.5

    @pytest.mark.asyncio
    async def test_mandatory_rule_fails(self):
        scheme = _make_scheme([
            _rule("annual_income", EligibilityOp.LTE, 100000, mandatory=True),
        ])
        result = await EligibilityEvaluator().evaluate(scheme, {"annual_income": 500000})
        assert result.eligible is False

    @pytest.mark.asyncio
    async def test_missing_mandatory_field(self):
        scheme = _make_scheme([
            _rule("caste_category", EligibilityOp.IN, ["sc", "st"], mandatory=True),
        ])
        result = await EligibilityEvaluator().evaluate(scheme, {"annual_income": 200000})
        assert result.eligible is False
        assert "caste_category" in result.missing_fields

    @pytest.mark.asyncio
    async def test_missing_optional_field_does_not_fail(self):
        scheme = _make_scheme([
            _rule("caste_category", EligibilityOp.IN, ["sc", "st"], mandatory=False),
            _rule("annual_income", EligibilityOp.LTE, 500000, mandatory=True),
        ])
        result = await EligibilityEvaluator().evaluate(scheme, {"annual_income": 200000})
        assert result.eligible is True

    @pytest.mark.asyncio
    async def test_age_boundary_exact(self):
        scheme = _make_scheme([
            _rule("age", EligibilityOp.GTE, 60, mandatory=True),
        ])
        result = await EligibilityEvaluator().evaluate(scheme, {"age": 60})
        assert result.eligible is True

        result2 = await EligibilityEvaluator().evaluate(scheme, {"age": 59})
        assert result2.eligible is False

    @pytest.mark.asyncio
    async def test_income_between(self):
        scheme = _make_scheme([
            _rule("annual_income", EligibilityOp.BETWEEN, [100000, 500000], mandatory=True),
        ])
        result = await EligibilityEvaluator().evaluate(scheme, {"annual_income": 300000})
        assert result.eligible is True

        result2 = await EligibilityEvaluator().evaluate(scheme, {"annual_income": 99999})
        assert result2.eligible is False

    @pytest.mark.asyncio
    async def test_in_operator(self):
        scheme = _make_scheme([
            _rule("caste_category", EligibilityOp.IN, ["sc", "st", "obc"]),
        ])
        assert (await EligibilityEvaluator().evaluate(scheme, {"caste_category": "sc"})).eligible is True
        assert (await EligibilityEvaluator().evaluate(scheme, {"caste_category": "general"})).eligible is False

    @pytest.mark.asyncio
    async def test_contains_operator(self):
        scheme = _make_scheme([
            _rule("occupation", EligibilityOp.CONTAINS, "farmer"),
        ])
        assert (await EligibilityEvaluator().evaluate(scheme, {"occupation": "small farmer"})).eligible is True
        assert (await EligibilityEvaluator().evaluate(scheme, {"occupation": "teacher"})).eligible is False

    @pytest.mark.asyncio
    async def test_no_rules(self):
        scheme = _make_scheme([])
        result = await EligibilityEvaluator().evaluate(scheme, {})
        assert result.eligible is False
