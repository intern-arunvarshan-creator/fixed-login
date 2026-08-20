"""Model and enum layer tests."""

from app.models.audit_log import AuditLog
from app.models.enums import (
    AuditAction,
    AuditActionFilter,
    AuditResourceType,
    AuditResourceTypeFilter,
    UserStatus,
    UserStatusFilter,
    resolve_filter,
)
from app.models.platform_admin import PlatformAdmin
from app.models.user import User


def test_user_status_values() -> None:
    assert UserStatus.ACTIVE == "active"
    assert UserStatus.INACTIVE == "inactive"


def test_audit_action_values() -> None:
    assert AuditAction.USER_CREATE == "user.create"
    assert AuditAction.LOGIN_SUCCESS == "auth.login.success"


def test_audit_resource_type_values() -> None:
    assert AuditResourceType.AUTH == "auth"
    assert AuditResourceType.USER == "user"


def test_filter_enums_mirror_base_values() -> None:
    assert UserStatusFilter.ACTIVE == UserStatus.ACTIVE
    assert UserStatusFilter.INACTIVE == UserStatus.INACTIVE
    assert AuditActionFilter.USER_CREATE == AuditAction.USER_CREATE
    assert AuditResourceTypeFilter.USER == AuditResourceType.USER


def test_resolve_filter_returns_none_for_all() -> None:
    assert resolve_filter(UserStatusFilter.ALL, UserStatus) is None
    assert resolve_filter(AuditActionFilter.ALL, AuditAction) is None


def test_resolve_filter_returns_base_member() -> None:
    assert resolve_filter(UserStatusFilter.ACTIVE, UserStatus) is UserStatus.ACTIVE
    assert resolve_filter(AuditActionFilter.USER_CREATE, AuditAction) is AuditAction.USER_CREATE
    assert resolve_filter(AuditResourceTypeFilter.AUTH, AuditResourceType) is AuditResourceType.AUTH


def test_user_defaults() -> None:
    user = User(name="Alice", email="alice@example.com", hashed_password="hash")
    assert user.status is UserStatus.ACTIVE
    assert user.id is not None
    assert user.created_at is not None


def test_platform_admin_fields() -> None:
    admin = PlatformAdmin(username="admin", hashed_password="hash")
    assert admin.username == "admin"


def test_audit_log_defaults() -> None:
    entry = AuditLog(action="user.create")
    assert entry.id is not None
    assert entry.actor is None
    assert entry.created_at is not None
