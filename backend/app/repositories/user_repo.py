from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func

from app.models.user import RefreshToken, Session, User, UserProfile
from app.repositories.base import BaseRepository
from app.core.exceptions import NotFoundError


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_profile(self, user_id: uuid.UUID) -> Optional[Tuple[User, UserProfile]]:
        stmt = (
            select(User)
            .options(joinedload(User.profile))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        user = result.unique().scalar_one_or_none()
        if user is None or user.profile is None:
            return None
        return user, user.profile

    async def increment_failed_logins(self, user_id: uuid.UUID) -> None:
        user = await self.get_by_id_or_fail(user_id)
        user.failed_login_count += 1
        if user.failed_login_count >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        await self.session.flush()

    async def reset_failed_logins(self, user_id: uuid.UUID) -> None:
        user = await self.get_by_id_or_fail(user_id)
        user.failed_login_count = 0
        user.locked_until = None
        await self.session.flush()


class SessionRepository(BaseRepository[Session]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Session, session)

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(Session)
            .where(
                and_(
                    Session.user_id == user_id,
                    Session.revoked == False,
                )
            )
        )
        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for s in sessions:
            s.revoked = True
            s.revoked_at = now
        await self.session.flush()
        return len(sessions)

    async def revoke_expired_sessions(self) -> int:
        stmt = (
            select(Session)
            .where(
                and_(
                    Session.expires_at < datetime.now(timezone.utc),
                    Session.revoked == False,
                )
            )
        )
        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for s in sessions:
            s.revoked = True
            s.revoked_at = now
        await self.session.flush()
        return len(sessions)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshToken, session)

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, token_id: uuid.UUID) -> None:
        token = await self.get_by_id_or_fail(token_id)
        token.used = True
        token.used_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def cleanup_expired(self) -> int:
        stmt = select(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.session.execute(stmt)
        tokens = list(result.scalars().all())
        for t in tokens:
            await self.session.delete(t)
        await self.session.flush()
        return len(tokens)


class ProfileRepository(BaseRepository[UserProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(UserProfile, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserProfile]:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **kwargs: Any) -> UserProfile:
        profile = await self.get_by_user_id(user_id)
        if profile:
            for key, value in kwargs.items():
                setattr(profile, key, value)
        else:
            profile = UserProfile(user_id=user_id, **kwargs)
            self.session.add(profile)
        await self.session.flush()
        return profile
