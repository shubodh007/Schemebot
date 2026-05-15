from __future__ import annotations

import hashlib
import secrets
import string
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt
from cryptography.fernet import Fernet

from app.core.config import Settings, settings
from app.core.logging import logger

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30
RESET_TOKEN_EXPIRE_HOURS = 1


def get_signing_key(override_key: Optional[str] = None) -> str:
    key = override_key or settings.secret_key
    if len(key) < 32:
        key = hashlib.sha256(key.encode()).hexdigest()
    return key


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
    override_key: Optional[str] = None,
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

    key = get_signing_key(override_key)
    return jwt.encode(payload, key, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: str,
    session_id: str,
    expires_delta: Optional[timedelta] = None,
    override_key: Optional[str] = None,
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

    key = get_signing_key(override_key)
    return jwt.encode(payload, key, algorithm=ALGORITHM)


def decode_token(
    token: str,
    verify_expiration: bool = True,
    override_key: Optional[str] = None,
) -> Dict[str, Any]:
    key = get_signing_key(override_key)
    try:
        payload = jwt.decode(
            token,
            key,
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


def generate_reset_token() -> Tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def generate_secure_id(length: int = 32) -> str:
    return secrets.token_hex(length)


def generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_api_key_fernet() -> Fernet:
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    return Fernet(Fernet.generate_key())


def encrypt_api_key(api_key: str) -> str:
    f = create_api_key_fernet()
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    f = create_api_key_fernet()
    return f.decrypt(encrypted.encode()).decode()
