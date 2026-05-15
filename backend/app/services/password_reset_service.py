from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GovSchemeError, NotFoundError
from app.core.logging import logger
from app.core.redis_client import RedisClient
from app.core.security import hash_password
from app.repositories.user_repo import UserRepository, SessionRepository


class ResetTokenInvalidError(GovSchemeError):
    status_code = 400
    code = "INVALID_RESET_TOKEN"
    detail = "Reset token is invalid or has expired"


class PasswordResetService:
    TOKEN_TTL = 900

    def __init__(self, session: AsyncSession, redis: RedisClient) -> None:
        self._session = session
        self._redis = redis
        self._user_repo = UserRepository(session)
        self._session_repo = SessionRepository(session)

    async def initiate_reset(self, email: str) -> None:
        user = await self._user_repo.get_by_email(email)
        if not user:
            logger.info("password_reset.email_not_found", email=email)
            return

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        await self._redis.set(
            f"pwd_reset:{token_hash}",
            str(user.id),
            ttl=self.TOKEN_TTL,
        )

        logger.info("password_reset.token_generated", user_id=str(user.id))

    async def validate_token(self, raw_token: str) -> UUID:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        user_id_str = await self._redis.get(f"pwd_reset:{token_hash}")
        if not user_id_str:
            raise ResetTokenInvalidError()
        return uuid.UUID(user_id_str)

    async def complete_reset(self, raw_token: str, new_password: str) -> None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        user_id_str = await self._redis.get(f"pwd_reset:{token_hash}")
        if not user_id_str:
            raise ResetTokenInvalidError()

        user_id = uuid.UUID(user_id_str)

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        await self._user_repo.update(user_id, password_hash=hash_password(new_password))
        await self._session_repo.revoke_all_user_sessions(user_id)
        await self._redis.delete(f"pwd_reset:{token_hash}")

        logger.info("password_reset.completed", user_id=str(user_id))
