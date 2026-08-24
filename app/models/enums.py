from enum import Enum, StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AdminStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AuditAction(StrEnum):
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_RESET_SUCCESS = "auth.password_reset.success"  # noqa: S105
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_REPLACE = "user.replace"
    USER_DELETE = "user.delete"


class AuditResourceType(StrEnum):
    AUTH = "auth"
    USER = "user"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    """Return the stored values for an enum (used by SQLAlchemy's SAEnum)."""
    return [str(member.value) for member in enum_cls]


# List-endpoint filter enums: each mirrors a base enum plus an ALL sentinel.
# Kept separate from the base enum so "All" never leaks into persisted data
# (e.g. a real user's status, or a recorded audit action).


class UserStatusFilter(StrEnum):
    ALL = "All"
    ACTIVE = UserStatus.ACTIVE.value
    INACTIVE = UserStatus.INACTIVE.value


class AuditActionFilter(StrEnum):
    ALL = "All"
    LOGIN_SUCCESS = AuditAction.LOGIN_SUCCESS.value
    LOGIN_FAILURE = AuditAction.LOGIN_FAILURE.value
    LOGOUT = AuditAction.LOGOUT.value
    PASSWORD_RESET_SUCCESS = AuditAction.PASSWORD_RESET_SUCCESS.value
    USER_CREATE = AuditAction.USER_CREATE.value
    USER_UPDATE = AuditAction.USER_UPDATE.value
    USER_REPLACE = AuditAction.USER_REPLACE.value
    USER_DELETE = AuditAction.USER_DELETE.value


class AuditResourceTypeFilter(StrEnum):
    ALL = "All"
    AUTH = AuditResourceType.AUTH.value
    USER = AuditResourceType.USER.value


def resolve_filter[T: StrEnum](value: StrEnum, base: type[T]) -> T | None:
    """Map a filter member to its base-enum member, or None for the ALL sentinel."""
    return None if value.name == "ALL" else base(value.value)
