"""Seed the RBAC catalog and backfill super_admin (idempotent).

Usage:
    uv run python app/database/scripts/seed_rbac.py
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

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
    role = await _get_or_create_role(db, SUPER_ADMIN_ROLE_NAME)
    for permission_name in PermissionName:
        await _get_or_create_permission(db, permission_name.value)
    await _grant_all_permissions(db, role.id)


async def assign_super_admin(db: AsyncSession, admin_id: uuid.UUID) -> None:
    """Ensure the given admin holds the super_admin role (no-op if already assigned)."""
    role = await _get_or_create_role(db, SUPER_ADMIN_ROLE_NAME)
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


async def _get_or_create_role(db: AsyncSession, name: str) -> Role:
    role = (await db.execute(select(Role).where(col(Role.name) == name))).scalar_one_or_none()
    if role is None:
        role = Role(name=name)
        db.add(role)
        await db.flush()
    return role


async def _get_or_create_permission(db: AsyncSession, name: str) -> Permission:
    permission = (
        await db.execute(select(Permission).where(col(Permission.name) == name))
    ).scalar_one_or_none()
    if permission is None:
        permission = Permission(name=name)
        db.add(permission)
        await db.flush()
    return permission


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
