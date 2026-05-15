from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from app.core.jwt_keys import get_signing_key

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

_private_key_pem: Optional[bytes] = None
_public_key_pem: Optional[bytes] = None


def _ensure_keys() -> None:
    global _private_key_pem, _public_key_pem
    if _private_key_pem is None:
        _private_key_pem, _public_key_pem = get_signing_key()


def get_private_key() -> bytes:
    _ensure_keys()
    return _private_key_pem  # type: ignore


def get_public_key() -> bytes:
    _ensure_keys()
    return _public_key_pem or _private_key_pem  # type: ignore


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: Dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16),
        "type": "access",
    }

    private_key = serialization.load_pem_private_key(
        get_private_key(),
        password=None,
        backend=default_backend(),
    )
    return jwt.encode(payload, private_key, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: str,
    session_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    payload: Dict[str, Any] = {
        "sub": user_id,
        "sid": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16),
        "type": "refresh",
    }

    private_key = serialization.load_pem_private_key(
        get_private_key(),
        password=None,
        backend=default_backend(),
    )
    return jwt.encode(payload, private_key, algorithm=ALGORITHM)


def decode_token(token: str, verify_expiration: bool = True) -> Dict[str, Any]:
    try:
        public_key = serialization.load_pem_public_key(
            get_public_key(),
            backend=default_backend(),
        )
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[ALGORITHM],
            options={"verify_exp": verify_expiration},
        )
        return payload
    except jwt.ExpiredSignatureError:
        from app.core.exceptions import TokenExpiredError
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        from app.core.exceptions import InvalidTokenError
        raise InvalidTokenError()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_secure_id(length: int = 32) -> str:
    return secrets.token_hex(length)


def generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))
