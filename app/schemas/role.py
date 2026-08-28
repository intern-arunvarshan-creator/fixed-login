import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Status
from app.utils.limits import DESCRIPTION_MAX_LENGTH, NAME_MAX_LENGTH, SCREEN_CODE_MAX_LENGTH

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
CODE_GRANTS_FETCHED = "S_200_ROL_GRANTS_FETCHED"
MSG_GRANTS_FETCHED = "Role grants fetched successfully"
CODE_GRANTS_UPDATED = "S_200_ROL_GRANTS_UPDATED"
MSG_GRANTS_UPDATED = "Role grants updated successfully"


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH, examples=["support-agent"])
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    status: Status = Status.ACTIVE


class RoleUpdate(BaseModel):
    """Partial update (PATCH) — only provided fields are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    status: Status | None = None


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: Status
    created_at: datetime
    updated_at: datetime


class RoleGrantItem(BaseModel):
    screen_code: str = Field(min_length=1, max_length=SCREEN_CODE_MAX_LENGTH)
    read: bool = False
    write: bool = False


class RoleGrantsUpdate(BaseModel):
    grants: list[RoleGrantItem]


class RoleGrantRead(BaseModel):
    screen_code: str
    screen_name: str
    sort_order: int
    read: bool
    write: bool


class RoleGrantsRead(BaseModel):
    grants: list[RoleGrantRead]
