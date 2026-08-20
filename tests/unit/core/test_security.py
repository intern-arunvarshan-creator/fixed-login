"""Security helper tests (hashing + tokens)."""

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("S3cureP@ss")
    assert hashed != "S3cureP@ss"
    assert verify_password("S3cureP@ss", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_long_password_is_truncated_to_72_bytes() -> None:
    long_password = "a" * 100
    hashed = hash_password(long_password)
    assert verify_password(long_password, hashed) is True


def test_access_token_round_trip() -> None:
    payload = decode_token(create_access_token("admin"))
    assert payload["sub"] == "admin"
    assert payload["type"] == "access"


def test_refresh_token_round_trip() -> None:
    payload = decode_token(create_refresh_token("admin"))
    assert payload["type"] == "refresh"


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(JWTError):
        decode_token("not-a-token")
