"""Query category service tests (repository mocked)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.exceptions import AppError, QueryCategoryKeyExistsError, QueryCategoryNotFoundError
from app.models.enums import Status
from app.models.query_category import QueryCategory
from app.schemas.query_category import QueryCategoryCreate, QueryCategoryUpdate
from app.services import query_category as query_category_service

ADMIN_ID = uuid.uuid4()


def _category(
    *,
    category_id: int = 1,
    key: str = "name",
) -> QueryCategory:
    return QueryCategory(
        id=category_id,
        module="KYC",
        type="personal",
        description="Personal details",
        key=key,
        label="Name",
        status=Status.ACTIVE,
        created_by=ADMIN_ID,
        updated_by=ADMIN_ID,
    )


async def test_create_category_success() -> None:
    data = QueryCategoryCreate(
        module="KYC",
        type="personal",
        description="Personal details",
        key="name",
        label="Name",
        status="active",
    )
    created = _category()

    with (
        patch.object(
            query_category_service.query_category,
            "get_category_by_key",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            query_category_service.query_category,
            "create_category",
            new=AsyncMock(return_value=created),
        ) as create_mock,
    ):
        result = await query_category_service.create_category(data, admin_id=ADMIN_ID)

    assert result.key == "name"
    create_mock.assert_awaited_once()
    assert create_mock.await_args.kwargs["admin_id"] == ADMIN_ID


async def test_create_category_duplicate_key() -> None:
    with patch.object(
        query_category_service.query_category,
        "get_category_by_key",
        new=AsyncMock(return_value=_category()),
    ):
        with pytest.raises(QueryCategoryKeyExistsError):
            await query_category_service.create_category(
                QueryCategoryCreate(
                    module="KYC",
                    type="personal",
                    key="name",
                    label="Name",
                ),
                admin_id=ADMIN_ID,
            )


async def test_get_category_found() -> None:
    category = _category()
    with patch.object(
        query_category_service.query_category,
        "get_category",
        new=AsyncMock(return_value=category),
    ):
        result = await query_category_service.get_category(1)
    assert result.id == 1


async def test_get_category_not_found() -> None:
    with patch.object(
        query_category_service.query_category,
        "get_category",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(QueryCategoryNotFoundError):
            await query_category_service.get_category(999)


async def test_list_categories() -> None:
    category = _category()
    with patch.object(
        query_category_service.query_category,
        "list_categories",
        new=AsyncMock(return_value=([category], 1)),
    ) as list_mock:
        items, total = await query_category_service.list_categories(
            page=2,
            limit=10,
            module="KYC",
            status=Status.ACTIVE,
        )

    assert len(items) == 1
    assert total == 1
    list_mock.assert_awaited_once_with(
        page=2,
        limit=10,
        module="KYC",
        status=Status.ACTIVE,
    )


async def test_update_category_success() -> None:
    category = _category()
    updated = _category(key="full_name")

    async def _apply(category, data, *, admin_id):
        for field, value in data.items():
            setattr(category, field, value)
        return category

    with (
        patch.object(
            query_category_service.query_category,
            "get_category",
            new=AsyncMock(return_value=category),
        ),
        patch.object(
            query_category_service.query_category,
            "get_category_by_key",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            query_category_service.query_category,
            "update_category",
            new=AsyncMock(side_effect=_apply),
        ) as update_mock,
    ):
        result = await query_category_service.update_category(
            1,
            QueryCategoryUpdate(key="full_name", label="Full Name"),
            admin_id=ADMIN_ID,
        )

    assert result.key == "full_name"
    payload = update_mock.await_args.kwargs["data"]
    assert payload["key"] == "full_name"
    assert payload["label"] == "Full Name"
    assert payload["updated_by"] == ADMIN_ID


async def test_update_category_not_found() -> None:
    with patch.object(
        query_category_service.query_category,
        "get_category",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(QueryCategoryNotFoundError):
            await query_category_service.update_category(
                999,
                QueryCategoryUpdate(label="New Label"),
                admin_id=ADMIN_ID,
            )


async def test_update_category_duplicate_key() -> None:
    category = _category()
    other = _category(category_id=2, key="signature_missing")

    with (
        patch.object(
            query_category_service.query_category,
            "get_category",
            new=AsyncMock(return_value=category),
        ),
        patch.object(
            query_category_service.query_category,
            "get_category_by_key",
            new=AsyncMock(return_value=other),
        ),
    ):
        with pytest.raises(QueryCategoryKeyExistsError):
            await query_category_service.update_category(
                1,
                QueryCategoryUpdate(key="signature_missing"),
                admin_id=ADMIN_ID,
            )


async def test_update_category_same_key_allowed() -> None:
    """Updating other fields while keeping the same key should not fail."""
    category = _category()

    with (
        patch.object(
            query_category_service.query_category,
            "get_category",
            new=AsyncMock(return_value=category),
        ),
        patch.object(
            query_category_service.query_category,
            "get_category_by_key",
            new=AsyncMock(return_value=category),
        ),
        patch.object(
            query_category_service.query_category,
            "update_category",
            new=AsyncMock(return_value=category),
        ) as update_mock,
    ):
        await query_category_service.update_category(
            1,
            QueryCategoryUpdate(key="name", label="Updated Name"),
            admin_id=ADMIN_ID,
        )

    update_mock.assert_awaited_once()


async def test_delete_category_success() -> None:
    category = _category()
    with (
        patch.object(
            query_category_service.query_category,
            "get_category",
            new=AsyncMock(return_value=category),
        ),
        patch.object(
            query_category_service.query_category,
            "delete_category",
            new=AsyncMock(),
        ) as delete_mock,
    ):
        await query_category_service.delete_category(1, admin_id=ADMIN_ID)

    delete_mock.assert_awaited_once_with(category, admin_id=ADMIN_ID)


async def test_delete_category_not_found() -> None:
    with patch.object(
        query_category_service.query_category,
        "get_category",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(QueryCategoryNotFoundError):
            await query_category_service.delete_category(999, admin_id=ADMIN_ID)