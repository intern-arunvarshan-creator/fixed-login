```python
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.query_category import QueryCategory
from app.models.schemas.query_category import (
    QueryCategoryCreate,
    QueryCategoryUpdate,
    QueryCategoryResponse,
)
from app.crud.services import QueryCategoryService


@pytest.fixture
def service():
    """Create a QueryCategoryService with a mocked repository."""
    service = QueryCategoryService.__new__(QueryCategoryService)
    service.repository = MagicMock()
    return service


@pytest.fixture
def category():
    """Sample QueryCategory model."""
    return QueryCategory(
        id=1,
        module="KYC",
        type="personal",
        description="Personal details",
        key="name",
        label="Name",
        status="active",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_category_success(service, category):
    """A category should be created when the key does not already exist."""
    service.repository.get_by_key.return_value = None
    service.repository.create.return_value = category

    data = QueryCategoryCreate(
        module="KYC",
        type="personal",
        description="Personal details",
        key="name",
        label="Name",
        status="active",
    )

    result = service.create_category(data)

    assert isinstance(result, QueryCategoryResponse)
    assert result.id == 1
    assert result.module == "KYC"
    assert result.key == "name"
    assert result.status == "active"

    service.repository.get_by_key.assert_called_once_with("name")
    service.repository.create.assert_called_once_with(data)


def test_create_category_duplicate_key(service, category):
    """Creating a category with an existing key should fail."""
    service.repository.get_by_key.return_value = category

    data = QueryCategoryCreate(
        module="KYC",
        type="personal",
        description="Personal details",
        key="name",
        label="Name",
        status="active",
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_category(data)

    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail

    service.repository.create.assert_not_called()


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


def test_get_category_by_id_success(service, category):
    """An existing category should be returned."""
    service.repository.get_by_id.return_value = category

    result = service.get_category_by_id(1)

    assert isinstance(result, QueryCategoryResponse)
    assert result.id == 1
    assert result.module == "KYC"
    assert result.type == "personal"
    assert result.key == "name"
    assert result.label == "Name"


def test_get_category_by_id_not_found(service):
    """Requesting a missing category should return 404."""
    service.repository.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service.get_category_by_id(999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_categories_success(service, category):
    """Categories should be returned with the total count."""
    service.repository.get_all.return_value = [category]
    service.repository.get_count.return_value = 1

    items, total = service.list_categories(
        page=1,
        limit=10,
        module="KYC",
        status="active",
    )

    assert len(items) == 1
    assert total == 1
    assert isinstance(items[0], QueryCategoryResponse)
    assert items[0].key == "name"

    service.repository.get_all.assert_called_once_with(
        skip=0,
        limit=10,
        module="KYC",
        status="active",
    )

    service.repository.get_count.assert_called_once_with(
        module="KYC",
        status="active",
    )


def test_list_categories_second_page(service, category):
    """Pagination should calculate the correct offset."""
    service.repository.get_all.return_value = [category]
    service.repository.get_count.return_value = 21

    items, total = service.list_categories(
        page=2,
        limit=10,
    )

    assert len(items) == 1
    assert total == 21

    service.repository.get_all.assert_called_once_with(
        skip=10,
        limit=10,
        module=None,
        status=None,
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_category_success(service, category):
    """An existing category should be updated successfully."""
    updated_category = QueryCategory(
        id=1,
        module="KYC",
        type="personal",
        description="Updated description",
        key="full_name",
        label="Full Name",
        status="active",
        created_at=category.created_at,
        updated_at=datetime(2026, 1, 2),
    )

    service.repository.get_by_id.return_value = category
    service.repository.get_by_key.return_value = None
    service.repository.update.return_value = updated_category

    data = QueryCategoryUpdate(
        description="Updated description",
        key="full_name",
        label="Full Name",
    )

    result = service.update_category(1, data)

    assert isinstance(result, QueryCategoryResponse)
    assert result.id == 1
    assert result.key == "full_name"
    assert result.label == "Full Name"

    service.repository.update.assert_called_once_with(1, data)


def test_update_category_not_found(service):
    """Updating a missing category should return 404."""
    service.repository.get_by_id.return_value = None

    data = QueryCategoryUpdate(label="New Label")

    with pytest.raises(HTTPException) as exc_info:
        service.update_category(999, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"

    service.repository.update.assert_not_called()


def test_update_category_duplicate_key(service, category):
    """Changing a category to an existing key should fail."""
    another_category = QueryCategory(
        id=2,
        module="RTO",
        type="signature",
        description="Signature",
        key="signature_missing",
        label="Signature Missing",
        status="active",
        created_at=category.created_at,
        updated_at=category.updated_at,
    )

    service.repository.get_by_id.return_value = category
    service.repository.get_by_key.return_value = another_category

    data = QueryCategoryUpdate(key="signature_missing")

    with pytest.raises(HTTPException) as exc_info:
        service.update_category(1, data)

    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail

    service.repository.update.assert_not_called()


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_category_success(service, category):
    """An existing category should be soft deleted."""
    service.repository.get_by_id.return_value = category
    service.repository.soft_delete.return_value = category

    result = service.delete_category(1)

    assert result is None

    service.repository.get_by_id.assert_called_once_with(1)
    service.repository.soft_delete.assert_called_once_with(1)


def test_delete_category_not_found(service):
    """Deleting a missing category should return 404."""
    service.repository.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service.delete_category(999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"

    service.repository.soft_delete.assert_not_called()


# ---------------------------------------------------------------------------
# Model -> Response conversion
# ---------------------------------------------------------------------------


def test_to_response(service, category):
    """SQLAlchemy model should be converted to QueryCategoryResponse."""
    result = service._to_response(category)

    assert isinstance(result, QueryCategoryResponse)
    assert result.id == category.id
    assert result.module == category.module
    assert result.type == category.type
    assert result.description == category.description
    assert result.key == category.key
    assert result.label == category.label
    assert result.status == category.status
    assert result.created_at == category.created_at
    assert result.updated_at == category.updated_at
```
