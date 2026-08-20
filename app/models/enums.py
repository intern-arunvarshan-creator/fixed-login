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
