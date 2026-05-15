from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository

security = HTTPBearer(auto_error=False)


async def current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        token = request.cookies.get("access_token")
        if token is None:
            raise AuthenticationError("Authentication required")
    else:
        token = credentials.credentials

    try:
        payload = decode_token(token)
    except AuthenticationError:
        raise

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")

    repo = UserRepository(session)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise AuthenticationError("User not found")

    request.state.user = user
    request.state.user_id = user.id
    request.state.user_role = user.role.value

    return user


async def optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    try:
        return await current_user(request, credentials, session)
    except AuthenticationError:
        return None


def require_role(required_role: UserRole) -> Callable:
    async def role_checker(user: User = Depends(current_user)) -> User:
        role_values = {
            UserRole.CITIZEN: 0,
            UserRole.ADMIN: 1,
            UserRole.SUPERADMIN: 2,
        }
        if role_values.get(user.role, 0) < role_values.get(required_role, 0):
            raise ForbiddenError(
                f"Role '{user.role.value}' does not have permission for this action"
            )
        return user

    return role_checker


require_admin = require_role(UserRole.ADMIN)
require_superadmin = require_role(UserRole.SUPERADMIN)
