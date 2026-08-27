"""Role business rules (CRUD, name uniqueness, protection)."""

import uuid

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.exceptions.exceptions import ProtectedResourceError, RoleNameExistsError, RoleNotFoundError
from app.models.enums import AuditAction, AuditResourceType, Status
from app.models.role import Role
from app.repositories import role_repository
from app.schemas.role import RoleCreate, RoleUpdate
from app.services import audit_service

SUPER_ADMIN_ROLE_NAME = "super_admin"


async def _ensure_name_available(name: str, exclude_id: uuid.UUID | None = None) -> None:
    existing = await role_repository.get_role_by_name(name)
    if existing is not None and (exclude_id is None or existing.id != exclude_id):
        raise RoleNameExistsError()


async def create_role(data: RoleCreate) -> Role:
    await _ensure_name_available(data.name)
    role = Role(name=data.name, description=data.description, status=data.status)
    role = await role_repository.create_role(role)
    await audit_service.record(
        action=AuditAction.ROLE_CREATE,
        resource_type=AuditResourceType.ROLE,
        resource_id=str(role.id),
        details={"name": role.name},
    )
    return role


async def list_roles(
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_PAGE_SIZE,
    search: str | None = None,
    status: Status | None = None,
) -> tuple[list[Role], int]:
    return await role_repository.list_roles(page=page, limit=limit, search=search, status=status)


async def get_role(role_id: uuid.UUID) -> Role:
    role = await role_repository.get_role(role_id)
    if role is None:
        raise RoleNotFoundError()
    return role


async def update_role(role_id: uuid.UUID, data: RoleUpdate) -> Role:
    role = await get_role(role_id)
    payload = data.model_dump(exclude_unset=True, exclude_none=True)
    if role.name == SUPER_ADMIN_ROLE_NAME:
        if "name" in payload and payload["name"] != SUPER_ADMIN_ROLE_NAME:
            raise ProtectedResourceError()
        if payload.get("status") == Status.INACTIVE:
            raise ProtectedResourceError()
    if "name" in payload:
        await _ensure_name_available(name=payload["name"], exclude_id=role_id)
    role = await role_repository.update_role(role=role, data=payload)
    await audit_service.record(
        action=AuditAction.ROLE_UPDATE,
        resource_type=AuditResourceType.ROLE,
        resource_id=str(role.id),
        details=data.model_dump(exclude_unset=True, exclude_none=True, mode="json"),
    )
    return role


async def delete_role(role_id: uuid.UUID) -> None:
    role = await get_role(role_id)
    if role.name == SUPER_ADMIN_ROLE_NAME:
        raise ProtectedResourceError()
    await role_repository.delete_role(role)
    await audit_service.record(
        action=AuditAction.ROLE_DELETE,
        resource_type=AuditResourceType.ROLE,
        resource_id=str(role_id),
    )
