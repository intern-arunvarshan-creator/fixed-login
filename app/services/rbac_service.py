"""RBAC business rules — effective permissions for a Platform Admin."""

import uuid

from app.core.tracing import traced
from app.repositories import rbac_repository


@traced("rbac_service.permissions_for_admin")
async def permissions_for_admin(admin_id: uuid.UUID) -> set[str]:
    grants = await rbac_repository.screen_grants_for_admin(admin_id)
    return _expand(grants)


def _expand(grants: set[tuple[str, bool, bool]]) -> set[str]:
    permissions: set[str] = set()
    for code, read, write in grants:
        if read or write:
            permissions.add(f"{code}.R")
        if write:
            permissions.add(f"{code}.W")
    return permissions


@traced("rbac_service.roles_for_admin")
async def roles_for_admin(admin_id: uuid.UUID) -> set[str]:
    return await rbac_repository.role_names_for_admin(admin_id)
