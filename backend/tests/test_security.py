from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import hash_password, verify_password, create_access_token, decode_token


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "SecurePass123!"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("CorrectPass1")
        assert verify_password("WrongPass1", hashed) is False

    def test_same_password_different_hash(self):
        pw = "SamePass123"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2
        assert verify_password(pw, h1) is True
        assert verify_password(pw, h2) is True


class TestJWTTokens:
    def test_create_and_decode(self):
        token = create_access_token("user-123", "citizen")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["role"] == "citizen"
        assert payload["type"] == "access"

    def test_expired_token_raises(self):
        import time
        token = create_access_token("user-123", "citizen", expires_delta=__import__("datetime").timedelta(seconds=-1))
        from app.core.exceptions import TokenExpiredError
        with pytest.raises(TokenExpiredError):
            decode_token(token)

    def test_invalid_signature_raises(self):
        from app.core.exceptions import InvalidTokenError
        with pytest.raises(InvalidTokenError):
            decode_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.dEaD")


@pytest.mark.asyncio
async def test_csrf_missing_on_post_returns_403(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/auth/logout",
        headers={k: v for k, v in auth_headers.items() if k != "X-CSRF-Token"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_csrf_token_set_on_get(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert "csrf_token" in response.cookies


@pytest.mark.asyncio
async def test_login_rate_limiting(client: AsyncClient):
    for _ in range(15):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
    assert response.status_code == 429
