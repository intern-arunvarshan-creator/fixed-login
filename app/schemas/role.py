import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Status

CODE_CREATED = "S_201_ROL_CREATED"
MSG_CREATED = "Role created successfully"
CODE_LISTED = "S_200_ROL_LIST_OK"
MSG_LISTED = "Roles fetched successfully"
CODE_FETCHED = "S_200_ROL_FETCH_OK"
MSG_FETCHED = "Role fetched successfully"
CODE_UPDATED = "S_200_ROL_UPDATED"
MSG_UPDATED = "Role updated successfully"
CODE_DELETED = "S_200_ROL_DELETED"
MSG_DELETED = "Role deleted successfully"


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, examples=["support-agent"])
    description: str | None = Field(default=None, max_length=255)
    status: Status = Status.ACTIVE


class RoleUpdate(BaseModel):
    """Partial update (PATCH) — only provided fields are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    status: Status | None = None


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: Status
    created_at: datetime
    updated_at: datetime
