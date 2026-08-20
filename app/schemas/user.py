import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserStatus
from app.schemas.common import Pagination

PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$")
PASSWORD_MIN_LENGTH = 8


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, pattern=PASSWORD_PATTERN)
    status: UserStatus = UserStatus.ACTIVE


class UserUpdate(BaseModel):
    """Partial update (PATCH) — only provided fields are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    status: UserStatus | None = None


class UserReplace(BaseModel):
    """Full replace (PUT) — name/email/password required; status unchanged."""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, pattern=PASSWORD_PATTERN)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class UserListData(BaseModel):
    data: list[UserRead]
    pagination: Pagination
