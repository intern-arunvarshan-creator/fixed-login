"""Role data access (all SQL)."""

import uuid
from typing import Any

from sqlalchemy import ColumnElement, and_, delete, func, select
from sqlmodel import col

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.database.session import get_session
from app.models.enums import Status
from app.models.role import Role
from app.models.role_screen import RoleScreen
from app.models.screen import Screen


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


async def screen_grants_for_role(role_id: uuid.UUID) -> list[tuple[str, str, int, bool, bool]]:
    """Return every active screen with this role's read/write flags (left join)."""
    db = get_session()
    result = await db.execute(
        select(
            col(Screen.code),
            col(Screen.name),
            col(Screen.sort_order),
            col(RoleScreen.read),
            col(RoleScreen.write),
        )
        .join(
            RoleScreen,
            and_(
                col(RoleScreen.screen_code) == col(Screen.code),
                col(RoleScreen.role_id) == role_id,
            ),
            isouter=True,
        )
        .where(col(Screen.status) == Status.ACTIVE)
        .order_by(col(Screen.sort_order), col(Screen.code))
    )
    rows: list[tuple[str, str, int, bool, bool]] = []
    for code, name, sort_order, read, write in result.all():
        rows.append((str(code), str(name), int(sort_order), bool(read), bool(write)))
    return rows


async def replace_role_grants(role_id: uuid.UUID, grants: list[RoleScreen]) -> None:
    """Replace the role's grants: delete all, insert the new set, in one commit."""
    db = get_session()
    await db.execute(delete(RoleScreen).where(col(RoleScreen.role_id) == role_id))
    db.add_all(grants)
    await db.commit()
