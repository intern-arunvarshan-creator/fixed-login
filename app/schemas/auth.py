from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.user import PasswordStr

CODE_LOGIN_OK = "S_200_AUTH_LOGIN_OK"
MSG_LOGIN_OK = "Login successful"
CODE_REFRESH_OK = "S_200_AUTH_REFRESH_OK"
MSG_REFRESH_OK = "Token refreshed"
CODE_OTP_SENT = "S_200_AUTH_OTP_SENT"
MSG_OTP_SENT = "OTP sent successfully"
CODE_OTP_VERIFIED = "S_200_AUTH_OTP_VERIFIED"
MSG_OTP_VERIFIED = "OTP verified successfully"
CODE_PASSWORD_UPDATED = "S_200_AUTH_PASSWORD_UPDATED"  # noqa: S105
MSG_PASSWORD_UPDATED = "Password updated successfully"  # noqa: S105
CODE_LOGOUT_OK = "S_200_AUTH_LOGOUT_OK"
MSG_LOGOUT_OK = "Logged out successfully"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, description="Admin account password (must not be empty)")


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105  ("bearer" is an OAuth token type, not a secret)


class GenerateOtpRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=1)


class UpdatePasswordRequest(BaseModel):
    email: EmailStr
    new_password: PasswordStr
    confirm_password: str = Field(min_length=1)

    @model_validator(mode="after")
    def _passwords_match(self) -> "UpdatePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match")
        return self
