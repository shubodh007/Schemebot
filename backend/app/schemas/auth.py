from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    email: str
    email_verified: bool
    role: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    caste_category: Optional[str] = None
    disability_status: str
    disability_percent: Optional[int] = None
    annual_income: Optional[float] = None
    state_code: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None
    is_farmer: bool
    is_bpl: bool
    marital_status: Optional[str] = None
    preferred_language: str
    profile_complete: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{9,14}$")
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    caste_category: Optional[str] = None
    disability_status: Optional[str] = None
    disability_percent: Optional[int] = Field(None, ge=0, le=100)
    annual_income: Optional[float] = Field(None, ge=0)
    state_code: Optional[str] = Field(None, min_length=2, max_length=2)
    district: Optional[str] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None
    is_farmer: Optional[bool] = None
    is_bpl: Optional[bool] = None
    marital_status: Optional[str] = None
    preferred_language: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    profile: ProfileResponse


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthMeResponse(BaseModel):
    user: UserResponse
    profile: ProfileResponse


class ErrorResponse(BaseModel):
    code: str
    detail: str
    errors: Optional[list[dict]] = None
    metadata: Optional[dict] = None
