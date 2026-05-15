from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountLockedError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    TokenExpiredError,
)
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User, UserProfile
from app.repositories.user_repo import (
    ProfileRepository,
    RefreshTokenRepository,
    SessionRepository,
    UserRepository,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.session_repo = SessionRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)
        self.profile_repo = ProfileRepository(session)

    async def register(
        self, email: str, password: str, full_name: str
    ) -> User:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError("A user with this email already exists")

        password_hashed = hash_password(password)
        user = await self.user_repo.create(
            email=email,
            password_hash=password_hashed,
        )

        await self.profile_repo.create(
            user_id=user.id,
            full_name=full_name,
        )

        logger.info("user.registered", user_id=str(user.id), email=email)
        return user

    async def login(
        self, email: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> Tuple[str, str, User, UserProfile]:
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise AuthenticationError("Invalid email or password")

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise AccountLockedError(user.locked_until.isoformat())

        if user.password_hash is None:
            raise AuthenticationError("This account uses social login. Please sign in with your provider.")

        if not verify_password(password, user.password_hash):
            await self.user_repo.increment_failed_logins(user.id)
            raise AuthenticationError("Invalid email or password")

        await self.user_repo.reset_failed_logins(user.id)

        session = await self.session_repo.create(
            user_id=user.id,
            access_token=create_access_token(str(user.id), user.role.value),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )

        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id), str(session.id))

        await self.refresh_repo.create(
            user_id=user.id,
            session_id=session.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        user.last_login_at = datetime.now(timezone.utc)
        if ip_address:
            user.last_login_ip = ip_address
        await self.session.flush()

        profile = await self.profile_repo.get_by_user_id(user.id)
        if profile is None:
            raise AuthenticationError("User profile not found")

        logger.info("user.login.success", user_id=str(user.id))
        return access_token, refresh_token, user, profile

    async def refresh_access_token(self, refresh_token: str) -> str:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])

        token_hash = hash_refresh_token(refresh_token)
        stored = await self.refresh_repo.get_by_hash(token_hash)
        if stored is None:
            raise TokenExpiredError()

        if stored.used:
            await self.session_repo.revoke_all_user_sessions(user_id)
            raise AuthenticationError("Refresh token has been used. All sessions revoked.")

        await self.refresh_repo.mark_used(stored.id)
        user = await self.user_repo.get_by_id_or_fail(user_id)

        new_access = create_access_token(str(user.id), user.role.value)
        new_refresh = create_refresh_token(str(user.id), str(session_id))

        await self.refresh_repo.create(
            user_id=user.id,
            session_id=session_id,
            token_hash=hash_refresh_token(new_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        await self.session.flush()
        return new_access

    async def logout(self, user_id: uuid.UUID, session_id: Optional[uuid.UUID] = None) -> None:
        if session_id:
            sess = await self.session_repo.get_by_id(session_id)
            if sess and str(sess.user_id) == str(user_id):
                sess.revoked = True
                sess.revoked_at = datetime.now(timezone.utc)
        else:
            await self.session_repo.revoke_all_user_sessions(user_id)
        await self.session.flush()

        logger.info("user.logout", user_id=str(user_id))
