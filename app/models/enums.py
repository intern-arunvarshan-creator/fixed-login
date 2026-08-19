from enum import Enum, StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    """Return the stored values for an enum (used by SQLAlchemy's SAEnum)."""
    return [str(member.value) for member in enum_cls]
