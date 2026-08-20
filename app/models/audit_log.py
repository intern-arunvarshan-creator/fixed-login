import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    actor: str | None = Field(default=None, max_length=255)
    action: str = Field(index=True, max_length=255)
    resource_type: str | None = Field(default=None, max_length=255)
    resource_id: str | None = Field(default=None, max_length=255)
    details: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    request_id: str | None = Field(default=None, max_length=255)
    ip_address: str | None = Field(default=None, max_length=255)
    user_agent: str | None = Field(default=None, max_length=512)
    created_at: datetime = Field(index=True, default_factory=utcnow)
