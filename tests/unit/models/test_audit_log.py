"""AuditLog model tests."""

from app.models.audit_log import AuditLog


def test_audit_log_defaults() -> None:
    entry = AuditLog(action="user.create")
    assert entry.id is not None
    assert entry.actor is None
    assert entry.created_at is not None
