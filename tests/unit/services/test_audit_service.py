"""Audit service tests (repositories mocked)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import audit_service


def test_record_is_best_effort_on_failure() -> None:
    with patch.object(
        audit_service.audit_repository,
        "create_audit_log",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        asyncio.run(audit_service.record(MagicMock(), actor="admin", action="user.create"))


def test_record_writes_entry() -> None:
    with patch.object(
        audit_service.audit_repository,
        "create_audit_log",
        new=AsyncMock(return_value=MagicMock()),
    ):
        asyncio.run(audit_service.record(MagicMock(), actor="admin", action="user.create"))


def test_list_audit_logs() -> None:
    with patch.object(
        audit_service.audit_repository,
        "list_audit_logs",
        new=AsyncMock(return_value=([], 0)),
    ):
        entries, total = asyncio.run(audit_service.list_audit_logs(MagicMock(), page=1, limit=20))
    assert entries == []
    assert total == 0
