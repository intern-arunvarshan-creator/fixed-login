"""Enum value tests."""

from app.models.enums import AuditAction, AuditResourceType, UserStatus


def test_user_status_values() -> None:
    assert UserStatus.ACTIVE == "active"
    assert UserStatus.INACTIVE == "inactive"


def test_audit_action_values() -> None:
    assert AuditAction.USER_CREATE == "user.create"
    assert AuditAction.LOGIN_SUCCESS == "auth.login.success"


def test_audit_resource_type_values() -> None:
    assert AuditResourceType.AUTH == "auth"
    assert AuditResourceType.USER == "user"
