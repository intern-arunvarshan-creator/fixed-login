"""Query category data access (all SQL)."""

from typing import Any
import uuid
from sqlalchemy import ColumnElement, func, select
from sqlmodel import col

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.database.session import get_session
from app.models.enums import Status
from app.models.query_category import QueryCategory


async def create_category(category: QueryCategory, *, admin_id: uuid.UUID) -> QueryCategory:
    category.created_by = admin_id
    db = get_session()
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def list_categories(
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_PAGE_SIZE,
    module: str | None = None,
    status: Status | None = None,
) -> tuple[list[QueryCategory], int]:
    db = get_session()
    filters: list[ColumnElement[bool]] = []

    if module:
        filters.append(col(QueryCategory.module) == module)
    if status is not None:
        filters.append(col(QueryCategory.status) == status)

    total = await db.scalar(
        select(func.count()).select_from(QueryCategory).where(*filters)
    )
    result = await db.execute(
        select(QueryCategory)
        .where(*filters)
        .order_by(col(QueryCategory.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(result.scalars().all()), total or 0


async def get_category(category_id: int) -> QueryCategory | None:
    return await get_session().get(QueryCategory, category_id)


async def get_category_by_key(key: str) -> QueryCategory | None:
    result = await get_session().execute(
        select(QueryCategory).where(col(QueryCategory.key) == key)
    )
    return result.scalar_one_or_none()


async def update_category(category: QueryCategory, data: dict[str, Any], *, admin_id: uuid.UUID) -> QueryCategory:
    db = get_session()
    for field, value in data.items():
        setattr(category, field, value)
    category.updated_by = admin_id
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(category: QueryCategory, *, admin_id: uuid.UUID) -> None:
    """Soft-delete: mark the category inactive rather than removing the row."""
    db = get_session()
    category.status = Status.INACTIVE
    category.updated_by = admin_id
    await db.commit()