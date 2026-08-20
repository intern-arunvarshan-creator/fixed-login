"""Auth service tests (repositories mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.errors import ApiError
from app.models.platform_admin import PlatformAdmin
from app.schemas.auth import LoginRequest, RefreshRequest
from app.services import auth_service


async def test_login_success() -> None:
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
        token = await auth_service.login(MagicMock(), LoginRequest(username="admin", password="pw"))
    assert token.access_token == "access"
    assert token.refresh_token == "refresh"


async def test_login_invalid_credentials() -> None:
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_username",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(ApiError):
            await auth_service.login(MagicMock(), LoginRequest(username="nope", password="pw"))


async def test_refresh_success() -> None:
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
        token = await auth_service.refresh(MagicMock(), RefreshRequest(refresh_token="r"))
    assert token.access_token == "access"
    assert token.refresh_token == "refresh"
