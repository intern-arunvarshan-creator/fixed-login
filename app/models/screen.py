"""Screen table — a named area of the admin UI, identified by a stable code."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class Screen(SQLModel, table=True):
    __tablename__ = "screens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=255)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=utcnow)
