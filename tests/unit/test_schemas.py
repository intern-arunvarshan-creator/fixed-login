"""Schema (DTO) layer tests."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.enums import UserStatus
from app.schemas.audit import AuditLogRead
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ApiResponse, Pagination
from app.schemas.user import UserCreate, UserRead


def test_login_request() -> None:
    assert LoginRequest(username="admin", password="pw").username == "admin"


def test_token_response_defaults() -> None:
    assert TokenResponse(access_token="a", refresh_token="r").token_type == "bearer"


def test_api_response_generic() -> None:
    assert ApiResponse[str](code="S", message="ok", data="x").data == "x"


def test_pagination_model() -> None:
    p = Pagination(page=1, limit=20, total_items=5, total_pages=1)
    assert p.total_items == 5


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


def test_audit_log_read() -> None:
    entry = AuditLogRead.model_validate(
        {
            "id": uuid.uuid4(),
            "actor": "admin",
            "action": "user.create",
            "resource_type": "user",
            "resource_id": "x",
            "details": None,
            "request_id": None,
            "ip_address": None,
            "user_agent": None,
            "created_at": datetime.now(UTC).replace(tzinfo=None),
        }
    )
    assert entry.action == "user.create"
