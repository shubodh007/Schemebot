from __future__ import annotations

import pytest
from app.services.scheme_service import SchemeService
from app.models.scheme import Scheme, SchemeEligibilityRule, EligibilityOp


@pytest.mark.asyncio
async def test_eligibility_exact_match(db_session):
    service = SchemeService(db_session)
    scheme = Scheme(
        title="Test Scheme",
        description="A test scheme",
        slug="test-scheme",
        level="central",
        status="active",
        source_url="https://example.com",
    )
    db_session.add(scheme)
    await db_session.flush()

    rule = SchemeEligibilityRule(
        scheme_id=scheme.id,
        field_name="annual_income",
        operator=EligibilityOp.LTE,
        value={"min": 0, "max": 300000},
        is_mandatory=True,
    )
    db_session.add(rule)
    await db_session.flush()

    profile = {"annual_income": 250000}
    result = await service.check_eligibility(
        user_id=scheme.id,
        profile_data=profile,
    )
    assert len(result["matches"]) > 0
    match = result["matches"][0]
    assert match.eligible is True
    assert match.score > 0


@pytest.mark.asyncio
async def test_eligibility_fails_when_rule_not_met(db_session):
    service = SchemeService(db_session)
    scheme = Scheme(
        title="Income Limited Scheme",
        description="Only for low income",
        slug="income-limited",
        level="central",
        status="active",
        source_url="https://example.com",
    )
    db_session.add(scheme)
    await db_session.flush()

    rule = SchemeEligibilityRule(
        scheme_id=scheme.id,
        field_name="annual_income",
        operator=EligibilityOp.LTE,
        value=100000,
        is_mandatory=True,
    )
    db_session.add(rule)
    await db_session.flush()

    result = await service.check_eligibility(
        user_id=scheme.id,
        profile_data={"annual_income": 500000},
    )
    match = result["matches"][0]
    assert match.eligible is False


@pytest.mark.asyncio
async def test_eligibility_missing_field_is_detected(db_session):
    service = SchemeService(db_session)
    scheme = Scheme(
        title="Caste Based Scheme",
        description="For SC/ST",
        slug="caste-based",
        level="central",
        status="active",
        source_url="https://example.com",
    )
    db_session.add(scheme)
    await db_session.flush()

    rule = SchemeEligibilityRule(
        scheme_id=scheme.id,
        field_name="caste_category",
        operator=EligibilityOp.IN,
        value=["sc", "st"],
        is_mandatory=True,
    )
    db_session.add(rule)
    await db_session.flush()

    result = await service.check_eligibility(
        user_id=scheme.id,
        profile_data={"annual_income": 200000},
    )
    match = result["matches"][0]
    assert len(match.missing_fields) > 0
    assert "caste_category" in match.missing_fields


@pytest.mark.asyncio
async def test_eligibility_age_boundary(db_session):
    service = SchemeService(db_session)
    scheme = Scheme(
        title="Senior Scheme",
        description="For elderly",
        slug="senior-scheme",
        level="central",
        status="active",
        source_url="https://example.com",
    )
    db_session.add(scheme)
    await db_session.flush()

    rule = SchemeEligibilityRule(
        scheme_id=scheme.id,
        field_name="age",
        operator=EligibilityOp.GTE,
        value=60,
        is_mandatory=True,
    )
    db_session.add(rule)
    await db_session.flush()

    result = await service.check_eligibility(
        user_id=scheme.id,
        profile_data={"age": 60},
    )
    assert result["matches"][0].eligible is True

    result2 = await service.check_eligibility(
        user_id=scheme.id,
        profile_data={"age": 59},
    )
    assert result2["matches"][0].eligible is False
