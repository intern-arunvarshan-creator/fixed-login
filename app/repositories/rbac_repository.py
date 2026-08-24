"""RBAC data access (all SQL) — resolve an admin's effective permissions."""

import uuid

from sqlalchemy import select
from sqlmodel import col

from app.database.session import get_session
from app.models.permission import Permission
from app.models.platform_admin_role import PlatformAdminRole
from app.models.role_permission import RolePermission


async def permission_names_for_admin(admin_id: uuid.UUID) -> set[str]:
    """Return the union of permission names granted to an admin via all their roles."""
    db = get_session()
    result = await db.execute(
        select(col(Permission.name))
        .join(RolePermission, col(RolePermission.permission_id) == col(Permission.id))
        .join(PlatformAdminRole, col(PlatformAdminRole.role_id) == col(RolePermission.role_id))
        .where(col(PlatformAdminRole.platform_admin_id) == admin_id)
    )
    return set(result.scalars().all())
