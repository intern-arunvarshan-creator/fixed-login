"""OTP repository tests (mocked session)."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.models.password_reset_otp import PasswordResetOtp
from app.repositories import otp_repository
from app.utils.time import utcnow


async def test_get() -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value="otp-row")
    with patch.object(otp_repository, "get_session", return_value=db):
        assert await otp_repository.get("admin@example.com") == "otp-row"


async def test_save() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    row = PasswordResetOtp(
        email="admin@example.com", expires_at=utcnow(), request_count=1, window_started_at=utcnow()
    )
    with patch.object(otp_repository, "get_session", return_value=db):
        assert await otp_repository.save(row) is row
    db.commit.assert_awaited_once()
