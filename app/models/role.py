"""Role table — a named set of Permissions assigned to a Platform Admin."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    description: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utcnow)
