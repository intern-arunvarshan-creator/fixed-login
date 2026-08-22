"""User repository tests (mocked async session)."""

import uuid
from unittest.mock import AsyncMock, MagicMock

from app.models.enums import UserStatus
from app.models.user import User
from app.repositories import user_repository


def _user() -> User:
    return User(
        id=uuid.uuid4(),
        email="alice@example.com",
        name="Alice",
        status=UserStatus.ACTIVE,
        hashed_password="hash",
    )


async def test_get_user_returns_none_when_missing() -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    assert await user_repository.get_user(db, uuid.uuid4()) is None


async def test_get_user_by_email() -> None:
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalar_one_or_none.return_value = "some-user"
    assert await user_repository.get_user_by_email(db, "a@b.com") == "some-user"


async def test_create_user_commits_and_refreshes() -> None:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    user = _user()
    result = await user_repository.create_user(db, user)
    assert result is user
    db.add.assert_called_once_with(user)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)


async def test_list_users_with_filters() -> None:
    db = MagicMock()
    db.scalar = AsyncMock(return_value=1)
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalars.return_value.all.return_value = []
    users, total = await user_repository.list_users(
        db, page=1, limit=20, search="a", status=UserStatus.ACTIVE
    )
    assert users == []
    assert total == 1


async def test_update_user_applies_fields_and_commits() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    user = _user()
    result = await user_repository.update_user(db, user, {"name": "Bob"})
    assert result is user
    assert user.name == "Bob"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)


async def test_delete_user_commits() -> None:
    db = MagicMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    user = _user()
    await user_repository.delete_user(db, user)
    db.delete.assert_awaited_once_with(user)
    db.commit.assert_awaited_once()
