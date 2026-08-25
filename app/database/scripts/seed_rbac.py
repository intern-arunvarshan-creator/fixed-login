"""Seed the RBAC catalog and backfill super_admin (idempotent)."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, col

from app.database.database import async_session_factory
from app.models.enums import PermissionName
from app.models.permission import Permission
from app.models.platform_admin import PlatformAdmin
from app.models.platform_admin_role import PlatformAdminRole
from app.models.role import Role
from app.models.role_permission import RolePermission

SUPER_ADMIN_ROLE_NAME = "super_admin"


async def ensure_catalog(db: AsyncSession) -> None:
    """Upsert the super_admin role, every known permission, and super_admin's grants."""
    role = await _get_or_create(db, Role, SUPER_ADMIN_ROLE_NAME)
    for permission_name in PermissionName:
        await _get_or_create(db, Permission, permission_name.value)
    await _grant_all_permissions(db, role.id)


async def assign_super_admin(db: AsyncSession, admin_id: uuid.UUID) -> None:
    """Ensure the given admin holds the super_admin role (no-op if already assigned)."""
    role = await _get_or_create(db, Role, SUPER_ADMIN_ROLE_NAME)
    existing = await db.execute(
        select(PlatformAdminRole).where(
            col(PlatformAdminRole.platform_admin_id) == admin_id,
            col(PlatformAdminRole.role_id) == role.id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(PlatformAdminRole(platform_admin_id=admin_id, role_id=role.id))


async def seed() -> None:
    """Seed the catalog and assign super_admin to every admin that has no roles."""
    async with async_session_factory() as db:
        await ensure_catalog(db)
        admins = (await db.execute(select(PlatformAdmin))).scalars().all()
        for admin in admins:
            await assign_super_admin(db, admin.id)
        await db.commit()
    print("RBAC catalog and super_admin assignments are ready.")


async def _get_or_create[T: SQLModel](db: AsyncSession, model: type[T], name: str) -> T:
    """Return the row with ``name``, creating (and flushing) it if absent."""
    # ``model`` is a generic SQLModel type, so the column is fetched by name
    # (ruff B009 prefers attribute access, which mypy rejects on ``type[T]``).
    name_column = getattr(model, "name")  # noqa: B009
    row = (await db.execute(select(model).where(col(name_column) == name))).scalar_one_or_none()
    if row is None:
        row = model(name=name)
        db.add(row)
        await db.flush()
    return row


async def _grant_all_permissions(db: AsyncSession, role_id: uuid.UUID) -> None:
    permissions = (await db.execute(select(Permission))).scalars().all()
    for permission in permissions:
        existing = await db.execute(
            select(RolePermission).where(
                col(RolePermission.role_id) == role_id,
                col(RolePermission.permission_id) == permission.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(RolePermission(role_id=role_id, permission_id=permission.id))


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
