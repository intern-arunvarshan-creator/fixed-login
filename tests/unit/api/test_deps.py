"""Auth dependency tests."""

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_admin
from app.core.security import create_access_token
from app.exceptions.errors import ApiError
from app.models.platform_admin import PlatformAdmin


async def test_get_current_admin_returns_admin() -> None:
    admin_id = uuid.uuid4()
    token = create_access_token(str(admin_id))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    db = AsyncMock()
    db.get = AsyncMock(
        return_value=PlatformAdmin(
            id=admin_id, username="admin", email="admin@example.com", hashed_password="hash"
        )
    )

    admin = await get_current_admin(credentials, db)
    assert admin.username == "admin"


async def test_get_current_admin_missing_credentials() -> None:
    db = AsyncMock()
    with pytest.raises(ApiError):
        await get_current_admin(None, db)


async def test_get_current_admin_rejects_non_uuid_subject() -> None:
    token = create_access_token("not-a-uuid")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    db = AsyncMock()
    with pytest.raises(ApiError):
        await get_current_admin(credentials, db)
