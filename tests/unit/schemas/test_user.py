"""User schema (DTO) tests."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.enums import UserStatus
from app.schemas.user import UserCreate, UserRead


def test_user_create_rejects_weak_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(name="Alice", email="alice@example.com", password="weak")


def test_user_create_defaults_to_active() -> None:
    user = UserCreate(name="Alice", email="alice@example.com", password="S3cureP@ss")
    assert user.status is UserStatus.ACTIVE


def test_user_read_from_attributes() -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    read = UserRead.model_validate(
        {
            "id": uuid.uuid4(),
            "name": "Alice",
            "email": "alice@example.com",
            "status": UserStatus.ACTIVE,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert read.name == "Alice"
