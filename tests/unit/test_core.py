"""Core + exception layer tests (security, errors)."""

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions.errors import (
    ApiError,
    email_already_registered,
    field_errors,
    invalid_credentials,
    not_authenticated,
    user_not_found,
    validation_failed,
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


def test_api_error_carries_fields() -> None:
    err = ApiError(404, "E_404", "Not found", {"x": 1})
    assert (err.status_code, err.code, err.message, err.data) == (
        404,
        "E_404",
        "Not found",
        {"x": 1},
    )


def test_field_errors_shape() -> None:
    assert field_errors([("email", "bad")]) == {"errors": [{"field": "email", "issue": "bad"}]}


def test_error_factories() -> None:
    assert user_not_found().status_code == 404
    assert email_already_registered().status_code == 409
    assert invalid_credentials().status_code == 401
    assert not_authenticated().status_code == 401
    assert validation_failed([("name", "short")]).status_code == 422
