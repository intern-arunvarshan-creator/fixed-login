"""Previous hashed passwords, kept to reject password reuse."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class PasswordHistory(SQLModel, table=True):
    __tablename__ = "password_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    platform_admin_id: uuid.UUID = Field(foreign_key="platform_admins.id", index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=utcnow)
