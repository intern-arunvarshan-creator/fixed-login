"""Audit service tests (repositories mocked)."""

from unittest.mock import AsyncMock, patch

from app.services import audit_service


async def test_record_is_best_effort_on_failure() -> None:
    with patch.object(
        audit_service.audit_repository,
        "create_audit_log",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        await audit_service.record(actor="admin", action="user.create")


async def test_record_writes_entry() -> None:
    with patch.object(
        audit_service.audit_repository,
        "create_audit_log",
        new=AsyncMock(return_value=None),
    ):
        await audit_service.record(actor="admin", action="user.create")


async def test_list_audit_logs() -> None:
    with patch.object(
        audit_service.audit_repository,
        "list_audit_logs",
        new=AsyncMock(return_value=([], 0)),
    ):
        entries, total = await audit_service.list_audit_logs(page=1, limit=20)
    assert entries == []
    assert total == 0


async def test_record_resolves_actor_from_context() -> None:
    from app.core.audit_context import reset_current_actor, set_current_actor

    captured: dict = {}

    async def _capture(**kwargs):
        captured.update(kwargs)
        return None

    token = set_current_actor("admin@example.com", "admin")
    try:
        with patch.object(
            audit_service.audit_repository,
            "create_audit_log",
            new=AsyncMock(side_effect=_capture),
        ):
            await audit_service.record(action="user.create")
    finally:
        reset_current_actor(token)
    assert captured["actor"] == "admin@example.com"
    assert captured["actor_type"] == "admin"


async def test_record_redacts_sensitive_fields() -> None:
    captured: dict = {}

    async def _capture(**kwargs):
        captured.update(kwargs)
        return None

    with patch.object(
        audit_service.audit_repository,
        "create_audit_log",
        new=AsyncMock(side_effect=_capture),
    ):
        await audit_service.record(
            actor="admin",
            action="user.update",
            details={"password": "s3cret", "name": "Bob"},
            payload={"access_token": "tok", "email": "a@b.c"},
            response={"refresh_token": "tok2", "status": "ok"},
        )
    assert captured["details"] == {"password": "***", "name": "Bob"}
    assert captured["payload"] == {"access_token": "***", "email": "a@b.c"}
    assert captured["response"] == {"refresh_token": "***", "status": "ok"}
