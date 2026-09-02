"""Query category business rules."""
from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.exceptions.exceptions import (
QueryCategoryKeyExistsError,
QueryCategoryNotFoundError,
)
from app.models.enums import Status
import uuid
from app.models.query_category import QueryCategory
from app.repositories import query_category
from app.schemas.query_category import QueryCategoryCreate, QueryCategoryUpdate

async def _ensure_key_available(
key: str,
exclude_id: int | None = None,
) -> None:
  existing = await query_category.get_category_by_key(key)


  if existing is not None and (
    exclude_id is None or existing.id != exclude_id
  ):
    raise QueryCategoryKeyExistsError()
 

async def create_category(data: QueryCategoryCreate, *, admin_id: uuid.UUID) -> QueryCategory:
    await _ensure_key_available(data.key)
    category = QueryCategory(
    module=data.module,
    type=data.type,
    description=data.description,
    updated_by=admin_id,
    created_by=admin_id,
    key=data.key,
    label=data.label,
    status=data.status,
)

    category = await query_category.create_category(category, admin_id=admin_id)

    return category

async def list_categories(
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_PAGE_SIZE,
    module: str | None = None,
    status: Status | None = None,
    ) -> tuple[list[QueryCategory], int]:
    return await query_category.list_categories(
        page=page,
        limit=limit,
        module=module,
        status=status,
)

async def get_category(category_id: int) -> QueryCategory:
    category = await query_category.get_category(category_id)

    if category is None:
        raise QueryCategoryNotFoundError()

    return category


async def update_category(category_id: int,data: QueryCategoryUpdate,*,
    admin_id: uuid.UUID,) -> QueryCategory:
    category = await get_category(category_id)


    payload = data.model_dump(
    exclude_unset=True,
    exclude_none=True,
    )
    if "key" in payload:
            await _ensure_key_available(
                        key=payload["key"],
                                exclude_id=category_id,
                                    )
    payload["updated_by"] = admin_id
    return await query_category.update_category(category=category, data=payload, admin_id=admin_id)


async def delete_category(category_id: int, *, admin_id: uuid.UUID) -> None:
    category = await get_category(category_id)
    await query_category.delete_category(category, admin_id=admin_id)

