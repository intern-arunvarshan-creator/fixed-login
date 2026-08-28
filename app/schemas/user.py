import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Status
from app.schemas.fields import EmailStr, NameStr, PasswordStr

CODE_CREATED = "S_201_USR_CREATED"
MSG_CREATED = "User created successfully"
CODE_LISTED = "S_200_USR_LIST_OK"
MSG_LISTED = "Users fetched successfully"
CODE_FETCHED = "S_200_USR_FETCH_OK"
MSG_FETCHED = "User fetched successfully"
CODE_UPDATED = "S_200_USR_UPDATED"
MSG_UPDATED = "User updated successfully"
CODE_DELETED = "S_200_USR_DELETED"
MSG_DELETED = "User deleted successfully"


class UserCreate(BaseModel):
    name: NameStr
    email: EmailStr
    password: PasswordStr
    status: Status = Status.ACTIVE


class UserUpdate(BaseModel):
    """Partial update (PATCH) — only provided fields are applied."""

    name: NameStr | None = None
    email: EmailStr | None = None
    status: Status | None = None


class UserReplace(BaseModel):
    """Full replace (PUT) — name/email/password required; status unchanged."""

    name: NameStr
    email: EmailStr
    password: PasswordStr


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    status: Status
    created_at: datetime
    updated_at: datetime
