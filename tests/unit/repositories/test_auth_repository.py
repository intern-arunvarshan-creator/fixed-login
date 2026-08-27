"""Auth repository tests (mocked session)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.platform_admin import PlatformAdmin
from app.repositories import auth_repository


async def test_get_admin_by_email() -> None:
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalar_one_or_none.return_value = "admin-object"
    with patch.object(auth_repository, "get_session", return_value=db):
        assert await auth_repository.get_admin_by_email("admin@example.com") == "admin-object"


async def test_get_admin_by_id() -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value="admin-object")
    with patch.object(auth_repository, "get_session", return_value=db):
        assert await auth_repository.get_admin_by_id(uuid.uuid4()) == "admin-object"


async def test_save_admin() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    admin = PlatformAdmin(username="admin", email="admin@example.com", hashed_password="hash")
    with patch.object(auth_repository, "get_session", return_value=db):
        assert await auth_repository.save_admin(admin) is admin
    db.commit.assert_awaited_once()
