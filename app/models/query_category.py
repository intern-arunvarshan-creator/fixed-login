import enum
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class StatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class QueryCategory(SQLModel, table=True):
    __tablename__ = "query_categories"

    id: int = Field(default=None, primary_key=True, index=True)
    module: str = Field(default=None, nullable=False)
    type: str = Field(default=None, nullable=False)
    description: str = Field(default=None, nullable=True)
    key: str = Field(default=None, unique=True, nullable=False)
    label: str = Field(default=None, nullable=False)
    status: StatusEnum = Field(default=StatusEnum.active, nullable=False)

    __table_args__ = (
        Index("idx_query_categories_module", "module"),
        Index("idx_query_categories_type", "type"),
        Index("idx_query_categories_status", "status"),
    )