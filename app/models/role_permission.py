"""Role → screen permission grant table — read/write booleans per screen."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True)
    screen_code: str = Field(foreign_key="screens.code", primary_key=True, max_length=50)
    read: bool = Field(default=False)
    write: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
