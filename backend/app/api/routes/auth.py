from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth_middleware import current_user
from app.core.database import get_session
from app.core.exceptions import AuthenticationError
from app.core.logging import logger
from app.models.user import User
from app.repositories.user_repo import ProfileRepository, SessionRepository
from app.schemas.auth import (
    AuthMeResponse,
    LoginRequest,
    LoginResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.schemas.auth import ErrorResponse  # noqa: F401

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    service = AuthService(session)
    user = await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return {
        "user": UserResponse.model_validate(user),
        "message": "Verify your email",
    }


@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    service = AuthService(session)
    access_token, refresh_token, user, profile = await service.login(
        email=body.email,
        password=body.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 24 * 60 * 60,
        path="/api/v1/auth/refresh",
    )

    return LoginResponse(
        access_token=access_token,
        expires_in=900,
        user=UserResponse.model_validate(user),
        profile=ProfileResponse.model_validate(profile),
    )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise AuthenticationError("Refresh token not found")

    service = AuthService(session)
    access_token = await service.refresh_access_token(refresh_token)

    return RefreshResponse(
        access_token=access_token,
        expires_in=900,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    sess_uuid = None
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        from app.core.security import decode_token
        try:
            payload = decode_token(refresh_token)
            import uuid
            sess_uuid = uuid.UUID(payload["sid"])
        except Exception:
            pass

    service = AuthService(session)
    await service.logout(user.id, sess_uuid)

    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")

    return {"detail": "Logged out successfully"}


@router.get("/me")
async def get_me(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    profile_repo = ProfileRepository(session)
    profile = await profile_repo.get_by_user_id(user.id)

    return AuthMeResponse(
        user=UserResponse.model_validate(user),
        profile=ProfileResponse.model_validate(profile) if profile else None,
    )


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    profile_repo = ProfileRepository(session)
    updated = await profile_repo.upsert(
        user_id=user.id,
        **body.model_dump(exclude_none=True),
    )
    return {"profile": ProfileResponse.model_validate(updated)}
