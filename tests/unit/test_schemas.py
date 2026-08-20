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


def test_login_request_allows_hyphen_in_middle() -> None:
    assert LoginRequest(username="john-doe", password="pw").username == "john-doe"


@pytest.mark.parametrize(
    "username",
    ["Admin!@$$", "-admin", "admin-", "ad--min", "ad min", ""],
)
def test_login_request_rejects_invalid_username_format(username: str) -> None:
    with pytest.raises(ValidationError):
        LoginRequest(username=username, password="pw")


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


def test_user_create_rejects_password_missing_complexity() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(name="Alice", email="alice@example.com", password="weakpassword")
    assert "must be at least 8 characters" in str(exc_info.value)


def test_user_create_password_schema_has_no_raw_regex() -> None:
    schema = UserCreate.model_json_schema()["properties"]["password"]
    assert "pattern" not in schema
    assert "must be at least 8 characters" in schema["description"]


def test_user_create_defaults_to_active() -> None:
    user = UserCreate(name="Alice", email="alice@example.com", password="S3cureP@ss")
    assert user.status is UserStatus.ACTIVE


def test_user_create_allows_hyphen_in_middle_of_name() -> None:
    user = UserCreate(name="Alice-Smith", email="alice@example.com", password="S3cureP@ss")
    assert user.name == "Alice-Smith"


@pytest.mark.parametrize(
    "name",
    ["Alice!", "-Alice", "Alice-", "Ali--ce", "Alice Smith"],
)
def test_user_create_rejects_invalid_name_format(name: str) -> None:
    with pytest.raises(ValidationError):
        UserCreate(name=name, email="alice@example.com", password="S3cureP@ss")


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
