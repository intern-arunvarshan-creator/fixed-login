"""Schema field-bound validation tests (empty and oversize rejection)."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    UpdatePasswordRequest,
    VerifyOtpRequest,
)
from app.schemas.role import RoleCreate
from app.schemas.screen import ScreenCreate
from app.schemas.user import UserCreate

VALID_PASSWORD = "S3cureP@ss"


def _rejects(model, **fields) -> None:
    with pytest.raises(ValidationError):
        model(**fields)


def test_refresh_token_rejects_empty() -> None:
    _rejects(RefreshRequest, refresh_token="")


def test_refresh_token_rejects_oversized() -> None:
    _rejects(RefreshRequest, refresh_token="x" * 2049)


def test_login_password_rejects_oversized() -> None:
    _rejects(LoginRequest, email="a@b.com", password="x" * 129)


def test_otp_rejects_oversized() -> None:
    _rejects(VerifyOtpRequest, email="a@b.com", otp="1" * 13)


def test_confirm_password_rejects_oversized() -> None:
    _rejects(
        UpdatePasswordRequest,
        email="a@b.com",
        new_password=VALID_PASSWORD,
        confirm_password="x" * 14,
    )


def test_email_rejects_oversized() -> None:
    _rejects(UserCreate, name="alice", email="a" * 300 + "@example.com", password=VALID_PASSWORD)


def test_name_rejects_oversized() -> None:
    _rejects(UserCreate, name="a" * 256, email="a@b.com", password=VALID_PASSWORD)


def test_description_rejects_oversized() -> None:
    _rejects(RoleCreate, name="support", description="d" * 256)


def test_sort_order_rejects_above_max() -> None:
    _rejects(ScreenCreate, name="Reports", sort_order=10000)


def test_sort_order_accepts_max() -> None:
    ScreenCreate(name="Reports", sort_order=9999)
