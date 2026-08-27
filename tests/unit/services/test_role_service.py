"""Role service tests (repositories mocked)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.exceptions import AppError
from app.models.enums import AuditAction, AuditResourceType, Status
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleGrantItem, RoleGrantsUpdate, RoleUpdate
from app.services import role_service


def _role(name: str = "support-agent") -> Role:
    return Role(id=uuid.uuid4(), name=name, description=None, status=Status.ACTIVE)


async def test_create_role() -> None:
    record = AsyncMock()
    with (
        patch.object(
            role_service.role_repository, "get_role_by_name", new=AsyncMock(return_value=None)
        ),
        patch.object(
            role_service.role_repository,
            "create_role",
            new=AsyncMock(side_effect=lambda role: role),
        ),
        patch.object(role_service.audit_service, "record", new=record),
    ):
        created = await role_service.create_role(RoleCreate(name="support-agent"))
    assert created.name == "support-agent"
    record.assert_awaited_once_with(
        action=AuditAction.ROLE_CREATE,
        resource_type=AuditResourceType.ROLE,
        resource_id=str(created.id),
        details={"name": "support-agent"},
    )


async def test_create_role_duplicate_name() -> None:
    with patch.object(
        role_service.role_repository, "get_role_by_name", new=AsyncMock(return_value=_role())
    ):
        with pytest.raises(AppError):
            await role_service.create_role(RoleCreate(name="support-agent"))


async def test_get_role_not_found() -> None:
    with patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=None)):
        with pytest.raises(AppError):
            await role_service.get_role(uuid.uuid4())


async def test_get_role_found() -> None:
    role = _role()
    with patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)):
        result = await role_service.get_role(role.id)
    assert result.id == role.id


async def test_list_roles() -> None:
    with patch.object(
        role_service.role_repository, "list_roles", new=AsyncMock(return_value=([], 0))
    ):
        roles, total = await role_service.list_roles(page=1, limit=20)
    assert roles == []
    assert total == 0


async def test_update_role() -> None:
    role = _role()
    record = AsyncMock()

    async def _apply(role, data):
        for key, value in data.items():
            setattr(role, key, value)
        return role

    with (
        patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)),
        patch.object(
            role_service.role_repository, "get_role_by_name", new=AsyncMock(return_value=None)
        ),
        patch.object(
            role_service.role_repository, "update_role", new=AsyncMock(side_effect=_apply)
        ),
        patch.object(role_service.audit_service, "record", new=record),
    ):
        result = await role_service.update_role(
            role_id=role.id, data=RoleUpdate(description="desc")
        )
    assert result.description == "desc"
    record.assert_awaited_once_with(
        action=AuditAction.ROLE_UPDATE,
        resource_type=AuditResourceType.ROLE,
        resource_id=str(role.id),
        details={"description": "desc"},
    )


async def test_update_super_admin_name_protected() -> None:
    role = _role(name="super_admin")
    with patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)):
        with pytest.raises(AppError):
            await role_service.update_role(role_id=role.id, data=RoleUpdate(name="renamed"))


async def test_update_super_admin_deactivate_protected() -> None:
    role = _role(name="super_admin")
    with patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)):
        with pytest.raises(AppError):
            await role_service.update_role(role_id=role.id, data=RoleUpdate(status=Status.INACTIVE))


async def test_delete_role() -> None:
    role = _role()
    record = AsyncMock()
    with (
        patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)),
        patch.object(role_service.role_repository, "delete_role", new=AsyncMock(return_value=None)),
        patch.object(role_service.audit_service, "record", new=record),
    ):
        await role_service.delete_role(role.id)
    record.assert_awaited_once_with(
        action=AuditAction.ROLE_DELETE,
        resource_type=AuditResourceType.ROLE,
        resource_id=str(role.id),
    )


async def test_delete_super_admin_protected() -> None:
    role = _role(name="super_admin")
    with patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)):
        with pytest.raises(AppError):
            await role_service.delete_role(role.id)


async def test_get_role_grants() -> None:
    role = _role()
    with (
        patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)),
        patch.object(
            role_service.role_repository,
            "screen_grants_for_role",
            new=AsyncMock(return_value=[("S1", "User Management", 1, True, False)]),
        ),
    ):
        grants = await role_service.get_role_grants(role.id)
    assert grants[0].screen_code == "S1"
    assert grants[0].read is True
    assert grants[0].write is False


async def test_update_role_grants_normalizes_write_implies_read() -> None:
    role = _role()
    record = AsyncMock()
    replace_mock = AsyncMock(return_value=None)
    with (
        patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)),
        patch.object(
            role_service.screen_repository,
            "active_screen_codes",
            new=AsyncMock(return_value={"S1", "S2"}),
        ),
        patch.object(role_service.role_repository, "replace_role_grants", new=replace_mock),
        patch.object(
            role_service.role_repository,
            "screen_grants_for_role",
            new=AsyncMock(return_value=[("S1", "User Management", 1, True, True)]),
        ),
        patch.object(role_service.audit_service, "record", new=record),
    ):
        grants = await role_service.update_role_grants(
            role.id,
            RoleGrantsUpdate(grants=[RoleGrantItem(screen_code="S1", read=False, write=True)]),
        )
    assert grants[0].read is True
    assert grants[0].write is True
    rows = replace_mock.await_args.args[1]
    assert rows[0].read is True
    assert rows[0].write is True


async def test_update_super_admin_grants_protected() -> None:
    role = _role(name="super_admin")
    with patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)):
        with pytest.raises(AppError):
            await role_service.update_role_grants(role.id, RoleGrantsUpdate(grants=[]))


async def test_update_role_grants_rejects_unknown_screen() -> None:
    role = _role()
    with (
        patch.object(role_service.role_repository, "get_role", new=AsyncMock(return_value=role)),
        patch.object(
            role_service.screen_repository,
            "active_screen_codes",
            new=AsyncMock(return_value={"S1"}),
        ),
    ):
        with pytest.raises(AppError):
            await role_service.update_role_grants(
                role.id,
                RoleGrantsUpdate(grants=[RoleGrantItem(screen_code="S9", read=True)]),
            )
