"""RBAC business rules — effective permissions for a Platform Admin."""

import uuid

from app.core.tracing import traced
from app.repositories import rbac_repository


@traced("rbac_service.permissions_for_admin")
async def permissions_for_admin(admin_id: uuid.UUID) -> set[str]:
    return await rbac_repository.permission_names_for_admin(admin_id)
