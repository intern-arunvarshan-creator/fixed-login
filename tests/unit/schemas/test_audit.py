"""Audit schema (DTO) tests."""

import uuid
from datetime import UTC, datetime

from app.schemas.audit import AuditLogRead


def test_audit_log_read() -> None:
    entry = AuditLogRead.model_validate(
        {
            "id": uuid.uuid4(),
            "actor": "admin",
            "action": "user.create",
            "resource_type": "user",
            "resource_id": "x",
            "details": None,
            "request_id": None,
            "ip_address": None,
            "user_agent": None,
            "created_at": datetime.now(UTC).replace(tzinfo=None),
        }
    )
    assert entry.action == "user.create"
