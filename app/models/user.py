import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, func
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.enums import UserStatus, enum_values


def _utcnow() -> datetime:
    """Naive UTC now (matches PostgreSQL ``timestamp without time zone``)."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    name: str = Field(max_length=255)
    status: UserStatus = Field(
        default=UserStatus.ACTIVE,
        sa_column=Column(
            SAEnum(UserStatus, name="user_status", values_callable=enum_values),
            nullable=False,
        ),
    )
    hashed_password: str
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow, sa_column_kwargs={"onupdate": func.now()})
