from enum import Enum, StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AuditAction(StrEnum):
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
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


def _filter_enum(name: str, base: type[Enum]) -> type[StrEnum]:
    """Build a StrEnum with an extra ALL member, for use as a list-endpoint filter default.

    Kept separate from the base enum so "All" never leaks into persisted data
    (e.g. a real user's status, or a recorded audit action).
    """
    members = {"ALL": "All", **{member.name: member.value for member in base}}
    return StrEnum(name, members)


UserStatusFilter = _filter_enum("UserStatusFilter", UserStatus)
AuditActionFilter = _filter_enum("AuditActionFilter", AuditAction)
AuditResourceTypeFilter = _filter_enum("AuditResourceTypeFilter", AuditResourceType)
