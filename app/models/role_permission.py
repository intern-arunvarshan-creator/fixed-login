"""Role → Permission grant table — which Permissions a Role allows."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True)
    permission_id: uuid.UUID = Field(foreign_key="permissions.id", primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
