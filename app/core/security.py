from datetime import UTC, datetime, timedelta
from typing import Any, cast

import bcrypt
from jose import jwt

from app.core.config import settings

# bcrypt only hashes the first 72 bytes; truncate explicitly because
# bcrypt >= 4.1 raises instead of silently truncating.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    truncated = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(truncated, hashed.encode("utf-8"))


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": now + expires_delta,
        "type": token_type,
    }
    return cast(str, jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm))


def create_access_token(subject: str) -> str:
    return _create_token(subject, "access", timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, "refresh", timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str) -> dict[str, Any]:
    """Decode a token. Raises ``jose.JWTError`` if invalid or expired."""
    return cast(
        dict[str, Any],
        jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm]),
    )
