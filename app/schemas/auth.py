from functools import partial
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from app.utils.validate import validate_username_format

CODE_LOGIN_OK = "S_200_AUTH_LOGIN_OK"
MSG_LOGIN_OK = "Login successful"
CODE_REFRESH_OK = "S_200_AUTH_REFRESH_OK"
MSG_REFRESH_OK = "Token refreshed"


class LoginRequest(BaseModel):
    username: Annotated[
        str, AfterValidator(partial(validate_username_format, field_label="Username"))
    ]
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105  ("bearer" is an OAuth token type, not a secret)
