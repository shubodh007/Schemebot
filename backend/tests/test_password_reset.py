from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_forgot_password_returns_200(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200
    assert "reset link" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_forgot_password_known_user(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user.email},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_with_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "this-is-a-completely-invalid-token-that-should-fail-validation-12345",
            "password": "NewPass1234",
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_RESET_TOKEN"


@pytest.mark.asyncio
async def test_validate_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/reset-password",
        params={"token": "invalid-token-that-will-fail-validation-1234567890"},
    )
    assert response.status_code == 400
