"""Password-reset OTP issuance state (expiry window + request throttle)."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class PasswordResetOtp(SQLModel, table=True):
    __tablename__ = "password_reset_otps"

    email: str = Field(primary_key=True, max_length=255)
    expires_at: datetime
    request_count: int = Field(default=0)
    window_started_at: datetime = Field(default_factory=utcnow)
