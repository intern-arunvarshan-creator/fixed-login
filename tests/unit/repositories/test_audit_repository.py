"""Audit repository tests (mocked async session)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.repositories import audit_repository


def test_create_audit_log_commits_and_refreshes() -> None:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    entry = asyncio.run(audit_repository.create_audit_log(db, actor="admin", action="user.create"))
    assert entry.action == "user.create"
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


def test_list_audit_logs_empty() -> None:
    db = MagicMock()
    db.scalar = AsyncMock(return_value=0)
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalars.return_value.all.return_value = []
    entries, total = asyncio.run(audit_repository.list_audit_logs(db, page=1, limit=20))
    assert entries == []
    assert total == 0
