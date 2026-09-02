"""Query category repository tests (mocked session)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.enums import Status
from app.models.query_category import QueryCategory
from app.repositories import query_category as query_category_repository

ADMIN_ID = uuid.uuid4()


def _category() -> QueryCategory:
    return QueryCategory(
        id=1,
        module="KYC",
        type="personal",
        description="Personal details",
        key="name",
        label="Name",
        status=Status.ACTIVE,
        created_by=ADMIN_ID,
        updated_by=ADMIN_ID,
    )


async def test_create_category_commits() -> None:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    category = _category()

    with patch.object(query_category_repository, "get_session", return_value=db):
        result = await query_category_repository.create_category(category, admin_id=ADMIN_ID)

    assert result is category
    assert category.created_by == ADMIN_ID
    db.add.assert_called_once_with(category)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(category)


async def test_get_category_returns_none_when_missing() -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    with patch.object(query_category_repository, "get_session", return_value=db):
        assert await query_category_repository.get_category(999) is None


async def test_get_category_by_key() -> None:
    category = _category()
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalar_one_or_none.return_value = category

    with patch.object(query_category_repository, "get_session", return_value=db):
        result = await query_category_repository.get_category_by_key("name")

    assert result is category


async def test_list_categories_with_filters() -> None:
    db = MagicMock()
    db.scalar = AsyncMock(return_value=1)
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalars.return_value.all.return_value = []

    with patch.object(query_category_repository, "get_session", return_value=db):
        categories, total = await query_category_repository.list_categories(
            page=2,
            limit=10,
            module="KYC",
            status=Status.ACTIVE,
        )

    assert categories == []
    assert total == 1
    db.scalar.assert_awaited_once()
    db.execute.assert_awaited_once()


async def test_list_categories_returns_zero_when_scalar_is_none() -> None:
    db = MagicMock()
    db.scalar = AsyncMock(return_value=None)
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalars.return_value.all.return_value = []

    with patch.object(query_category_repository, "get_session", return_value=db):
        _, total = await query_category_repository.list_categories()

    assert total == 0


async def test_update_category_applies_fields_and_commits() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    category = _category()

    with patch.object(query_category_repository, "get_session", return_value=db):
        result = await query_category_repository.update_category(
            category,
            {"label": "Full Name"},
            admin_id=ADMIN_ID,
        )

    assert result is category
    assert category.label == "Full Name"
    assert category.updated_by == ADMIN_ID
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(category)


async def test_delete_category_soft_deletes() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    category = _category()

    with patch.object(query_category_repository, "get_session", return_value=db):
        await query_category_repository.delete_category(category, admin_id=ADMIN_ID)

    assert category.status is Status.INACTIVE
    assert category.updated_by == ADMIN_ID
    db.commit.assert_awaited_once()