from pydantic import BaseModel, Field, model_validator

from app.schemas.fields import EmailStr, PasswordStr
from app.utils.limits import (
    CONFIRM_PASSWORD_MAX_LENGTH,
    LOGIN_PASSWORD_MAX_LENGTH,
    OTP_MAX_LENGTH,
    REFRESH_TOKEN_MAX_LENGTH,
)

CODE_LOGIN_OK = "S_200_AUTH_LOGIN_OK"
MSG_LOGIN_OK = "Logged in successfully"
CODE_REFRESH_OK = "S_200_AUTH_REFRESH_OK"
MSG_REFRESH_OK = "Token refreshed"
CODE_OTP_SENT = "S_200_AUTH_OTP_SENT"
MSG_OTP_SENT = "OTP sent successfully"
CODE_OTP_VERIFIED = "S_200_AUTH_OTP_VERIFIED"
MSG_OTP_VERIFIED = "OTP verified successfully"
# Response-code constants — "password" here names a response, not a stored secret.
CODE_PASSWORD_UPDATED = "S_200_AUTH_PASSWORD_UPDATED"  # noqa: S105  # nosec B105
MSG_PASSWORD_UPDATED = "Password updated successfully"  # noqa: S105  # nosec B105
CODE_LOGOUT_OK = "S_200_AUTH_LOGOUT_OK"
MSG_LOGOUT_OK = "Logged out successfully"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1, max_length=LOGIN_PASSWORD_MAX_LENGTH, description="Admin account password"
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=REFRESH_TOKEN_MAX_LENGTH)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105  ("bearer" is an OAuth token type, not a secret)


class GenerateOtpRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=1, max_length=OTP_MAX_LENGTH)


class UpdatePasswordRequest(BaseModel):
    email: EmailStr
    new_password: PasswordStr
    confirm_password: str = Field(min_length=1, max_length=CONFIRM_PASSWORD_MAX_LENGTH)

    @model_validator(mode="after")
    def _passwords_match(self) -> "UpdatePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match")
        return self
