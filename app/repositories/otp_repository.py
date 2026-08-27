"""Password-reset OTP state (all SQL)."""

from app.database.session import get_session
from app.models.password_reset_otp import PasswordResetOtp


async def get(email: str) -> PasswordResetOtp | None:
    return await get_session().get(PasswordResetOtp, email)


async def save(row: PasswordResetOtp) -> PasswordResetOtp:
    db = get_session()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
