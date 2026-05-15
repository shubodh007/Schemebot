from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.redis_client import redis_client
from app.services.password_reset_service import PasswordResetService

router = APIRouter(prefix="/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=32)
    password: str = Field(..., min_length=8, max_length=128)


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    body: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = PasswordResetService(session, redis_client)
    await service.initiate_reset(body.email)
    return {"detail": "If an account exists with this email, a reset link has been sent"}


@router.get("/reset-password", status_code=200)
async def validate_reset_token(
    token: str = Query(..., min_length=32),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = PasswordResetService(session, redis_client)
    await service.validate_token(token)
    return {"valid": True}


@router.post("/reset-password", status_code=200)
async def complete_reset(
    body: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = PasswordResetService(session, redis_client)
    await service.complete_reset(body.token, body.password)
    return {"detail": "Password has been reset. All sessions have been invalidated."}
