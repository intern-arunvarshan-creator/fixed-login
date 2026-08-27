"""Role business rules (CRUD, name uniqueness, protection)."""

import uuid

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.exceptions.exceptions import (
    ProtectedResourceError,
    RoleNameExistsError,
    RoleNotFoundError,
    ValidationError,
    field_errors,
)
from app.models.enums import AuditAction, AuditResourceType, Status
from app.models.role import Role
from app.models.role_screen import RoleScreen
from app.repositories import role_repository, screen_repository
from app.schemas.role import RoleCreate, RoleGrantRead, RoleGrantsUpdate, RoleUpdate
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


async def get_role_grants(role_id: uuid.UUID) -> list[RoleGrantRead]:
    await get_role(role_id)
    rows = await role_repository.screen_grants_for_role(role_id)
    return [
        RoleGrantRead(
            screen_code=code, screen_name=name, sort_order=sort_order, read=read, write=write
        )
        for code, name, sort_order, read, write in rows
    ]


async def update_role_grants(role_id: uuid.UUID, data: RoleGrantsUpdate) -> list[RoleGrantRead]:
    role = await get_role(role_id)
    if role.name == SUPER_ADMIN_ROLE_NAME:
        raise ProtectedResourceError()
    grants_by_code: dict[str, tuple[bool, bool]] = {}
    for item in data.grants:
        grants_by_code[item.screen_code] = (item.read or item.write, item.write)
    valid = await screen_repository.active_screen_codes()
    invalid = [code for code in grants_by_code if code not in valid]
    if invalid:
        raise ValidationError(
            data=field_errors(
                [("screen_code", f"Unknown or inactive screen: {code}") for code in invalid]
            )
        )
    rows = [
        RoleScreen(role_id=role_id, screen_code=code, read=read, write=write)
        for code, (read, write) in grants_by_code.items()
    ]
    await role_repository.replace_role_grants(role_id, rows)
    await audit_service.record(
        action=AuditAction.ROLE_GRANTS_UPDATE,
        resource_type=AuditResourceType.ROLE,
        resource_id=str(role_id),
        details={
            "grants": [
                {"screen_code": code, "read": read, "write": write}
                for code, (read, write) in sorted(grants_by_code.items())
            ]
        },
    )
    return await get_role_grants(role_id)
