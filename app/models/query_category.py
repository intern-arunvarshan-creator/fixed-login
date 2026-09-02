from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, Index, Text, func
from sqlmodel import Field, SQLModel
import uuid
from app.models.enums import Status, enum_values


class QueryCategory(SQLModel, table=True):
    __tablename__ = "query_categories"
    __table_args__ = (
        Index("idx_query_categories_module", "module"),
        Index("idx_query_categories_type", "type"),
        Index("idx_query_categories_status", "status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    module: str = Field(nullable=False)
    type: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)
    key: str = Field(nullable=False, unique=True, index=True)
    label: str = Field(nullable=False)

    status: Status = Field(
        default=Status.ACTIVE,
        sa_column=Column(
            SAEnum(
                Status,
                values_callable=enum_values,  # stores/reads "active", "inactive"
                name="status",
                create_type=False,  # type already exists from other tables
            ),
            nullable=False,
            server_default=Status.ACTIVE.value,
        ),
    )

    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    created_by: uuid.UUID = Field(foreign_key="platform_admins.id", nullable=False)
    updated_by: uuid.UUID = Field(foreign_key="platform_admins.id", nullable=False)