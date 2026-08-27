"""Screen service tests (repositories mocked)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.exceptions import AppError
from app.models.enums import AuditAction, AuditResourceType, Status
from app.models.role import Role
from app.models.screen import Screen
from app.schemas.screen import ScreenCreate, ScreenUpdate
from app.services import screen_service


def _screen(code: str = "S5", name: str = "Reports") -> Screen:
    return Screen(id=uuid.uuid4(), code=code, name=name, sort_order=0, status=Status.ACTIVE)


def _super_admin() -> Role:
    return Role(id=uuid.uuid4(), name="super_admin", status=Status.ACTIVE)


async def test_create_screen_auto_generates_code() -> None:
    record = AsyncMock()
    with (
        patch.object(
            screen_service.screen_repository, "next_screen_code", new=AsyncMock(return_value="S5")
        ),
        patch.object(
            screen_service.screen_repository,
            "get_screen_by_code",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            screen_service.role_repository,
            "get_role_by_name",
            new=AsyncMock(return_value=_super_admin()),
        ),
        patch.object(
            screen_service.screen_repository,
            "create_screen",
            new=AsyncMock(side_effect=lambda screen, **kwargs: screen),
        ),
        patch.object(screen_service.audit_service, "record", new=record),
    ):
        created = await screen_service.create_screen(ScreenCreate(name="Reports"))
    assert created.code == "S5"
    record.assert_awaited_once_with(
        action=AuditAction.SCREEN_CREATE,
        resource_type=AuditResourceType.SCREEN,
        resource_id="S5",
        details={"code": "S5", "name": "Reports"},
    )


async def test_create_screen_grants_super_admin() -> None:
    admin = _super_admin()
    created = _screen()
    with (
        patch.object(
            screen_service.screen_repository,
            "get_screen_by_code",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            screen_service.role_repository,
            "get_role_by_name",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(
            screen_service.screen_repository, "create_screen", new=AsyncMock(return_value=created)
        ) as create_mock,
        patch.object(screen_service.audit_service, "record", new=AsyncMock()),
    ):
        await screen_service.create_screen(ScreenCreate(name="Reports", code="S5"))
    create_mock.assert_awaited_once()
    assert create_mock.call_args.kwargs["super_admin_role_id"] == admin.id


async def test_create_screen_duplicate_code() -> None:
    with patch.object(
        screen_service.screen_repository,
        "get_screen_by_code",
        new=AsyncMock(return_value=_screen()),
    ):
        with pytest.raises(AppError):
            await screen_service.create_screen(ScreenCreate(name="Reports", code="S5"))


async def test_get_screen_not_found() -> None:
    with patch.object(
        screen_service.screen_repository, "get_screen", new=AsyncMock(return_value=None)
    ):
        with pytest.raises(AppError):
            await screen_service.get_screen(uuid.uuid4())


async def test_list_screens() -> None:
    with patch.object(
        screen_service.screen_repository, "list_screens", new=AsyncMock(return_value=([], 0))
    ):
        screens, total = await screen_service.list_screens(page=1, limit=20)
    assert screens == []
    assert total == 0


async def test_update_screen() -> None:
    screen = _screen()
    record = AsyncMock()

    async def _apply(screen, data):
        for key, value in data.items():
            setattr(screen, key, value)
        return screen

    with (
        patch.object(
            screen_service.screen_repository, "get_screen", new=AsyncMock(return_value=screen)
        ),
        patch.object(
            screen_service.screen_repository, "update_screen", new=AsyncMock(side_effect=_apply)
        ),
        patch.object(screen_service.audit_service, "record", new=record),
    ):
        result = await screen_service.update_screen(
            screen_id=screen.id, data=ScreenUpdate(name="New")
        )
    assert result.name == "New"
    record.assert_awaited_once_with(
        action=AuditAction.SCREEN_UPDATE,
        resource_type=AuditResourceType.SCREEN,
        resource_id="S5",
        details={"name": "New"},
    )


async def test_update_protected_screen_deactivate_raises() -> None:
    screen = _screen(code="S1")
    with patch.object(
        screen_service.screen_repository, "get_screen", new=AsyncMock(return_value=screen)
    ):
        with pytest.raises(AppError):
            await screen_service.update_screen(
                screen_id=screen.id, data=ScreenUpdate(status=Status.INACTIVE)
            )


async def test_delete_screen() -> None:
    screen = _screen()
    record = AsyncMock()
    with (
        patch.object(
            screen_service.screen_repository, "get_screen", new=AsyncMock(return_value=screen)
        ),
        patch.object(
            screen_service.screen_repository, "delete_screen", new=AsyncMock(return_value=None)
        ),
        patch.object(screen_service.audit_service, "record", new=record),
    ):
        await screen_service.delete_screen(screen.id)
    record.assert_awaited_once_with(
        action=AuditAction.SCREEN_DELETE,
        resource_type=AuditResourceType.SCREEN,
        resource_id="S5",
    )


async def test_delete_protected_screen_raises() -> None:
    screen = _screen(code="S4")
    with patch.object(
        screen_service.screen_repository, "get_screen", new=AsyncMock(return_value=screen)
    ):
        with pytest.raises(AppError):
            await screen_service.delete_screen(screen.id)
