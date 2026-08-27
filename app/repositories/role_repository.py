"""Role data access (all SQL)."""

import uuid
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlmodel import col

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.database.session import get_session
from app.models.enums import Status
from app.models.role import Role


async def create_role(role: Role) -> Role:
    db = get_session()
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def list_roles(
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_PAGE_SIZE,
    search: str | None = None,
    status: Status | None = None,
) -> tuple[list[Role], int]:
    db = get_session()
    filters: list[ColumnElement[bool]] = []
    if search:
        pattern = f"%{search}%"
        filters.append(col(Role.name).ilike(pattern))
    if status is not None:
        filters.append(col(Role.status) == status)

    total = await db.scalar(select(func.count()).select_from(Role).where(*filters))
    result = await db.execute(
        select(Role)
        .where(*filters)
        .order_by(col(Role.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(result.scalars().all()), total or 0


async def get_role(role_id: uuid.UUID) -> Role | None:
    return await get_session().get(Role, role_id)


async def get_role_by_name(name: str) -> Role | None:
    result = await get_session().execute(select(Role).where(col(Role.name) == name))
    return result.scalar_one_or_none()


async def update_role(role: Role, data: dict[str, Any]) -> Role:
    db = get_session()
    for field, value in data.items():
        setattr(role, field, value)
    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(role: Role) -> None:
    """Soft-delete: mark the role inactive rather than removing the row."""
    db = get_session()
    role.status = Status.INACTIVE
    await db.commit()
