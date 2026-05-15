from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SchemeCategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon_name: Optional[str] = None
    sort_order: int

    model_config = {"from_attributes": True}


class EligibilityRuleResponse(BaseModel):
    id: UUID
    field_name: str
    operator: str
    value: dict
    is_mandatory: bool
    description: Optional[str] = None
    sort_order: int

    model_config = {"from_attributes": True}


class SchemeCard(BaseModel):
    id: UUID
    title: str
    title_hi: Optional[str] = None
    title_te: Optional[str] = None
    slug: str
    description: str
    category: Optional[SchemeCategoryResponse] = None
    level: str
    state_code: Optional[str] = None
    status: str
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SchemeDetail(BaseModel):
    id: UUID
    title: str
    title_hi: Optional[str] = None
    title_te: Optional[str] = None
    slug: str
    description: str
    description_hi: Optional[str] = None
    description_te: Optional[str] = None
    category: Optional[SchemeCategoryResponse] = None
    ministry: Optional[str] = None
    department: Optional[str] = None
    level: str
    state_code: Optional[str] = None
    status: str
    launch_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_allocated: Optional[float] = None
    beneficiaries_count: Optional[int] = None
    application_url: Optional[str] = None
    guidelines_url: Optional[str] = None
    portal_url: Optional[str] = None
    source_url: Optional[str] = None
    tags: list[str]
    metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SchemeDetailWithEligibility(SchemeDetail):
    eligibility_rules: list[EligibilityRuleResponse] = []


class SchemeListResponse(BaseModel):
    schemes: list[SchemeCard]
    total: int
    page: int
    has_more: bool


class ProfileOverride(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    caste_category: Optional[str] = None
    disability_status: Optional[str] = None
    disability_percent: Optional[int] = Field(None, ge=0, le=100)
    annual_income: Optional[float] = Field(None, ge=0)
    state_code: Optional[str] = None
    district: Optional[str] = None
    is_farmer: Optional[bool] = None
    is_bpl: Optional[bool] = None


class EligibilityMatch(BaseModel):
    scheme: SchemeCard
    score: float = Field(..., ge=0, le=1)
    eligible: bool
    matching_rules: list[str]
    failing_rules: list[str]
    missing_fields: list[str]


class EligibilityCheckRequest(BaseModel):
    profile_override: Optional[ProfileOverride] = None


class EligibilityCheckResponse(BaseModel):
    matches: list[EligibilityMatch]
    checked_at: datetime
    profile_completeness: float = Field(..., ge=0, le=1)


class SchemeEligibilityResponse(BaseModel):
    eligible: bool
    score: float = Field(..., ge=0, le=1)
    reasons: list[str]
    missing_fields: list[str]


class SaveSchemeRequest(BaseModel):
    notes: Optional[str] = None
    reminder_date: Optional[date] = None


class SavedSchemeResponse(BaseModel):
    id: UUID
    scheme: SchemeCard
    notes: Optional[str] = None
    reminder_date: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompareSchemesRequest(BaseModel):
    scheme_ids: list[UUID] = Field(..., min_length=2, max_length=6)
    name: Optional[str] = None


class ComparisonResult(BaseModel):
    id: UUID
    name: Optional[str] = None
    schemes: list[SchemeDetail]
    comparison_fields: list[str]
    created_at: datetime
