"""Password history repository tests (mocked session)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.password_history import PasswordHistory
from app.repositories import password_history_repository
from app.utils.time import utcnow


async def test_add() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(return_value="row")
    admin_id = uuid.uuid4()
    with patch.object(password_history_repository, "get_session", return_value=db):
        result = await password_history_repository.add(admin_id, "hashed", utcnow())
    assert result.platform_admin_id == admin_id
    assert result.hashed_password == "hashed"
    db.commit.assert_awaited_once()


async def test_recent_for_admin() -> None:
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalars.return_value.all.return_value = ["a", "b"]
    with patch.object(password_history_repository, "get_session", return_value=db):
        assert await password_history_repository.recent_for_admin(uuid.uuid4(), 3) == ["a", "b"]


async def test_trim_deletes_old_entries() -> None:
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    row = PasswordHistory(platform_admin_id=uuid.uuid4(), hashed_password="hash")
    with (
        patch.object(password_history_repository, "get_session", return_value=db),
        patch.object(
            password_history_repository,
            "recent_for_admin",
            new=AsyncMock(return_value=[row]),
        ),
    ):
        await password_history_repository.trim(row.platform_admin_id, keep=3)
    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()
