"""Password-reset OTP state (all SQL)."""

from sqlalchemy import delete as sa_delete
from sqlmodel import col

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


async def delete(email: str) -> None:
    """Remove the OTP row after a successful reset (single-use)."""
    db = get_session()
    await db.execute(sa_delete(PasswordResetOtp).where(col(PasswordResetOtp.email) == email))
    await db.commit()
