"""Service layer tests (repositories mocked)."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.errors import ApiError
from app.models.enums import UserStatus
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest
from app.schemas.user import UserCreate, UserUpdate
from app.services import audit_service, auth_service, user_service


def _user(email: str = "alice@example.com") -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        name="Alice",
        status=UserStatus.ACTIVE,
        hashed_password="hash",
    )


# --- auth_service ---


def test_login_success() -> None:
    admin = PlatformAdmin(username="admin", hashed_password="hash")
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_username",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=True),
        patch.object(auth_service, "create_access_token", return_value="access"),
        patch.object(auth_service, "create_refresh_token", return_value="refresh"),
    ):
        token = asyncio.run(
            auth_service.login(MagicMock(), LoginRequest(username="admin", password="pw"))
        )
    assert token.access_token == "access"
    assert token.refresh_token == "refresh"


def test_login_invalid_credentials() -> None:
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_username",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(ApiError):
            asyncio.run(
                auth_service.login(MagicMock(), LoginRequest(username="nope", password="pw"))
            )


def test_refresh_success() -> None:
    admin = PlatformAdmin(username="admin", hashed_password="hash")
    with (
        patch.object(
            auth_service, "decode_token", return_value={"type": "refresh", "sub": "admin"}
        ),
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_username",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "create_access_token", return_value="access"),
        patch.object(auth_service, "create_refresh_token", return_value="refresh"),
    ):
        token = asyncio.run(auth_service.refresh(MagicMock(), RefreshRequest(refresh_token="r")))
    assert token.access_token == "access"
    assert token.refresh_token == "refresh"


# --- user_service ---


def test_create_user() -> None:
    with (
        patch.object(
            user_service.user_repository,
            "get_user_by_email",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            user_service.user_repository,
            "create_user",
            new=AsyncMock(side_effect=lambda db, user: user),
        ),
        patch.object(user_service, "hash_password", return_value="hashed"),
    ):
        created = asyncio.run(
            user_service.create_user(
                MagicMock(),
                UserCreate(name="Alice", email="alice@example.com", password="S3cureP@ss"),
            )
        )
    assert created.email == "alice@example.com"
    assert created.hashed_password == "hashed"


def test_create_user_duplicate_email() -> None:
    with patch.object(
        user_service.user_repository,
        "get_user_by_email",
        new=AsyncMock(return_value=_user()),
    ):
        with pytest.raises(ApiError):
            asyncio.run(
                user_service.create_user(
                    MagicMock(),
                    UserCreate(name="Alice", email="alice@example.com", password="S3cureP@ss"),
                )
            )


def test_get_user_not_found() -> None:
    with patch.object(user_service.user_repository, "get_user", new=AsyncMock(return_value=None)):
        with pytest.raises(ApiError):
            asyncio.run(user_service.get_user(MagicMock(), uuid.uuid4()))


def test_get_user_found() -> None:
    user = _user()
    with patch.object(user_service.user_repository, "get_user", new=AsyncMock(return_value=user)):
        result = asyncio.run(user_service.get_user(MagicMock(), user.id))
    assert result.id == user.id


def test_update_user_applies_fields() -> None:
    user = _user()

    async def _apply(db, u, payload):
        for key, value in payload.items():
            setattr(u, key, value)
        return u

    with (
        patch.object(user_service.user_repository, "get_user", new=AsyncMock(return_value=user)),
        patch.object(
            user_service.user_repository,
            "get_user_by_email",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            user_service.user_repository, "update_user", new=AsyncMock(side_effect=_apply)
        ),
    ):
        result = asyncio.run(user_service.update_user(MagicMock(), user.id, UserUpdate(name="Bob")))
    assert result.name == "Bob"


def test_delete_user() -> None:
    user = _user()
    with (
        patch.object(user_service.user_repository, "get_user", new=AsyncMock(return_value=user)),
        patch.object(user_service.user_repository, "delete_user", new=AsyncMock(return_value=None)),
    ):
        asyncio.run(user_service.delete_user(MagicMock(), user.id))


# --- audit_service ---


def test_record_is_best_effort_on_failure() -> None:
    with patch.object(
        audit_service.audit_repository,
        "create_audit_log",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        asyncio.run(audit_service.record(MagicMock(), actor="admin", action="user.create"))


def test_record_writes_entry() -> None:
    with patch.object(
        audit_service.audit_repository,
        "create_audit_log",
        new=AsyncMock(return_value=MagicMock()),
    ):
        asyncio.run(audit_service.record(MagicMock(), actor="admin", action="user.create"))


def test_list_audit_logs() -> None:
    with patch.object(
        audit_service.audit_repository,
        "list_audit_logs",
        new=AsyncMock(return_value=([], 0)),
    ):
        entries, total = asyncio.run(audit_service.list_audit_logs(MagicMock(), page=1, limit=20))
    assert entries == []
    assert total == 0
