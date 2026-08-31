"""Auth service tests (repositories mocked)."""

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from jose import JWTError

from app.exceptions.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    AuthenticationError,
    AuthTimeoutError,
    InvalidCredentialsError,
    InvalidOtpError,
    OtpThrottledError,
    PasswordResetFailedError,
    PasswordReuseError,
)
from app.models.enums import Status
from app.models.password_history import PasswordHistory
from app.models.password_reset_otp import PasswordResetOtp
from app.models.platform_admin import PlatformAdmin
from app.schemas.auth import (
    GenerateOtpRequest,
    LoginRequest,
    RefreshRequest,
    UpdatePasswordRequest,
    VerifyOtpRequest,
)
from app.services import auth_service
from app.utils.time import utcnow


def _admin(**overrides: object) -> PlatformAdmin:
    fields: dict[str, object] = {
        "id": uuid.uuid4(),
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": "hash",
        "status": Status.ACTIVE,
    }
    fields.update(overrides)
    # mypy can't narrow a dict[str, object] into each field's type; the overrides
    # are valid values for their keyed field, so the ignore is deliberate.
    return PlatformAdmin(**fields)  # type: ignore[arg-type]


async def test_login_success() -> None:
    admin = _admin()
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=True),
        patch.object(
            auth_service.rbac_service,
            "permissions_for_admin",
            new=AsyncMock(return_value={"S1.R", "S1.W", "S2.R"}),
        ),
        patch.object(
            auth_service.rbac_service,
            "roles_for_admin",
            new=AsyncMock(return_value={"super_admin"}),
        ),
        patch.object(auth_service, "create_access_token", return_value="access"),
        patch.object(auth_service, "create_refresh_token", return_value="refresh"),
        patch.object(auth_service, "decode_token", return_value={"jti": "r1"}),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        token = await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
    assert token.access_token == "access"
    assert token.refresh_token == "refresh"
    assert admin.current_refresh_jti == "r1"


async def test_login_invalid_credentials() -> None:
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_email",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.login(LoginRequest(email="nope@example.com", password="pw"))
    assert exc_info.value.message == "Invalid user credentials."
    assert exc_info.value.data is None


async def test_login_inactive_account() -> None:
    admin = _admin(status=Status.INACTIVE)
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=True),
    ):
        with pytest.raises(AccountInactiveError):
            await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))


async def test_login_wrong_password_increments_counter() -> None:
    admin = _admin()
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=False),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
    assert exc_info.value.code == "E_401_AUTH_INVALID_CREDENTIALS"
    assert exc_info.value.data == {"remaining_attempts": 4}
    assert "4 attempts remaining" in exc_info.value.message
    assert admin.failed_login_attempts == 1


async def test_login_wrong_password_last_attempt_before_lock() -> None:
    admin = _admin(failed_login_attempts=3)
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=False),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
    assert exc_info.value.data == {"remaining_attempts": 1}
    assert "1 attempt remaining" in exc_info.value.message
    assert admin.failed_login_attempts == 4


async def test_login_locks_account_at_max_attempts() -> None:
    admin = _admin(failed_login_attempts=4)
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=False),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        with pytest.raises(AccountLockedError):
            await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
    assert admin.locked_until is not None
    assert admin.failed_login_attempts == 0


async def test_login_rejects_locked_account() -> None:
    admin = _admin(locked_until=utcnow() + timedelta(minutes=10))
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=True) as verify,
    ):
        with pytest.raises(AccountLockedError):
            await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
        verify.assert_not_called()


async def test_login_times_out_without_incrementing_fail_count() -> None:
    admin = _admin()
    save = AsyncMock(return_value=admin)
    with (
        patch.object(auth_service.settings, "auth_service_timeout_seconds", 0.01),
        patch.object(auth_service.settings, "auth_service_delay", 0.05),
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=save,
        ),
    ):
        with pytest.raises(AuthTimeoutError) as exc_info:
            await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
    assert exc_info.value.code == "E_504_AUTH_TIMEOUT"
    assert exc_info.value.status_code == 504
    assert admin.failed_login_attempts == 0
    save.assert_not_called()


async def test_login_resets_counter_on_success() -> None:
    admin = _admin(failed_login_attempts=3)
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=True),
        patch.object(
            auth_service.rbac_service,
            "permissions_for_admin",
            new=AsyncMock(return_value={"S1.R"}),
        ),
        patch.object(
            auth_service.rbac_service,
            "roles_for_admin",
            new=AsyncMock(return_value={"super_admin"}),
        ),
        patch.object(auth_service, "create_access_token", return_value="access"),
        patch.object(auth_service, "create_refresh_token", return_value="refresh"),
        patch.object(auth_service, "decode_token", return_value={"jti": "r1"}),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
    assert admin.failed_login_attempts == 0
    assert admin.locked_until is None


async def test_refresh_success_rotates_session() -> None:
    admin_id = uuid.uuid4()
    admin = _admin(id=admin_id, current_refresh_jti="r1")
    with (
        patch.object(
            auth_service,
            "decode_token",
            side_effect=[
                {"type": "refresh", "user_id": str(admin_id), "jti": "r1"},
                {"jti": "r2"},
            ],
        ),
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_id",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(
            auth_service.rbac_service,
            "permissions_for_admin",
            new=AsyncMock(return_value={"S1.R", "S1.W", "S2.R"}),
        ),
        patch.object(
            auth_service.rbac_service,
            "roles_for_admin",
            new=AsyncMock(return_value={"super_admin"}),
        ),
        patch.object(auth_service, "create_access_token", return_value="access"),
        patch.object(auth_service, "create_refresh_token", return_value="refresh"),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        token = await auth_service.refresh(RefreshRequest(refresh_token="r"))
    assert token.access_token == "access"
    assert token.refresh_token == "refresh"
    assert admin.current_refresh_jti == "r2"


async def test_refresh_rejects_malformed_subject() -> None:
    with patch.object(
        auth_service, "decode_token", return_value={"type": "refresh", "user_id": "not-a-uuid"}
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.refresh(RefreshRequest(refresh_token="r"))


async def test_refresh_rejects_wrong_token_type() -> None:
    with patch.object(
        auth_service, "decode_token", return_value={"type": "access", "user_id": str(uuid.uuid4())}
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.refresh(RefreshRequest(refresh_token="r"))


async def test_refresh_rejects_invalid_token() -> None:
    with patch.object(auth_service, "decode_token", side_effect=JWTError("bad token")):
        with pytest.raises(AuthenticationError):
            await auth_service.refresh(RefreshRequest(refresh_token="r"))


async def test_refresh_rejects_unknown_admin() -> None:
    with (
        patch.object(
            auth_service,
            "decode_token",
            return_value={"type": "refresh", "user_id": str(uuid.uuid4())},
        ),
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_id",
            new=AsyncMock(return_value=None),
        ),
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.refresh(RefreshRequest(refresh_token="r"))


async def test_get_admin_from_payload_rejects_wrong_access_session() -> None:
    admin = _admin(current_refresh_jti="r2")
    payload = {"type": "access", "user_id": str(admin.id), "jti": "a1", "rjti": "r1"}
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_id",
        new=AsyncMock(return_value=admin),
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.get_admin_from_payload(payload)


async def test_get_admin_from_payload_rejects_missing_session() -> None:
    admin = _admin(current_refresh_jti=None)
    payload = {"type": "refresh", "user_id": str(admin.id), "jti": "r1"}
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_id",
        new=AsyncMock(return_value=admin),
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.get_admin_from_payload(payload)


async def test_get_admin_from_payload_accepts_current_access() -> None:
    admin = _admin(current_refresh_jti="r1")
    payload = {"type": "access", "user_id": str(admin.id), "jti": "a1", "rjti": "r1"}
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_id",
        new=AsyncMock(return_value=admin),
    ):
        result = await auth_service.get_admin_from_payload(payload)
    assert result is admin


async def test_logout_clears_session_pointer() -> None:
    admin_id = uuid.uuid4()
    admin = _admin(id=admin_id, current_refresh_jti="r1")
    payload = {"type": "access", "user_id": str(admin_id)}
    with (
        patch.object(auth_service, "decode_token", return_value=payload),
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_id",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        await auth_service.logout(access_token="access-token")
    assert admin.current_refresh_jti is None


async def test_get_admin_by_id_returns_admin() -> None:
    admin = _admin()
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_id",
        new=AsyncMock(return_value=admin),
    ):
        result = await auth_service.get_admin_by_id(admin.id)
    assert result is admin


async def test_get_admin_by_id_unknown_raises() -> None:
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_id",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.get_admin_by_id(uuid.uuid4())


async def test_get_admin_by_id_inactive_raises() -> None:
    admin = _admin(status=Status.INACTIVE)
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_id",
        new=AsyncMock(return_value=admin),
    ):
        with pytest.raises(AccountInactiveError):
            await auth_service.get_admin_by_id(admin.id)


async def test_generate_otp_returns_for_unknown_admin() -> None:
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_email",
        new=AsyncMock(return_value=None),
    ):
        await auth_service.generate_otp(GenerateOtpRequest(email="nope@example.com"))


async def test_generate_otp_returns_for_inactive_admin() -> None:
    admin = _admin(status=Status.INACTIVE)
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_email",
        new=AsyncMock(return_value=admin),
    ):
        await auth_service.generate_otp(GenerateOtpRequest(email="admin@example.com"))


async def test_generate_otp_creates_row_for_active_admin() -> None:
    admin = _admin()
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=None)),
        patch.object(auth_service.otp_repository, "save", new=AsyncMock(return_value=None)) as save,
    ):
        await auth_service.generate_otp(GenerateOtpRequest(email="admin@example.com"))
    save.assert_awaited_once()
    created = save.await_args.args[0]
    assert isinstance(created, PasswordResetOtp)
    assert created.request_count == 1


async def test_generate_otp_increments_within_window() -> None:
    admin = _admin()
    now = utcnow()
    row = PasswordResetOtp(
        email="admin@example.com", expires_at=now, request_count=1, window_started_at=now
    )
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=row)),
        patch.object(auth_service.otp_repository, "save", new=AsyncMock(return_value=None)) as save,
    ):
        await auth_service.generate_otp(GenerateOtpRequest(email="admin@example.com"))
    assert row.request_count == 2
    save.assert_awaited_once()


async def test_generate_otp_throttles_at_limit() -> None:
    admin = _admin()
    now = utcnow()
    row = PasswordResetOtp(
        email="admin@example.com", expires_at=now, request_count=3, window_started_at=now
    )
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=row)),
    ):
        with pytest.raises(OtpThrottledError):
            await auth_service.generate_otp(GenerateOtpRequest(email="admin@example.com"))


async def test_generate_otp_resets_window_after_expiry() -> None:
    admin = _admin()
    row = PasswordResetOtp(
        email="admin@example.com",
        expires_at=utcnow(),
        request_count=3,
        window_started_at=utcnow() - timedelta(minutes=20),
    )
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=row)),
        patch.object(auth_service.otp_repository, "save", new=AsyncMock(return_value=None)) as save,
    ):
        await auth_service.generate_otp(GenerateOtpRequest(email="admin@example.com"))
    assert row.request_count == 1
    save.assert_awaited_once()


async def test_verify_otp_accepts_correct_otp() -> None:
    admin = _admin()
    row = PasswordResetOtp(
        email="admin@example.com",
        expires_at=utcnow() + timedelta(minutes=5),
        request_count=1,
        window_started_at=utcnow(),
    )
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=row)),
        patch.object(auth_service.otp_repository, "save", new=AsyncMock(return_value=row)) as save,
    ):
        await auth_service.verify_otp(VerifyOtpRequest(email="admin@example.com", otp="12345"))
    assert row.verified is True
    save.assert_awaited_once()


async def test_verify_otp_rejects_wrong_otp() -> None:
    admin = _admin()
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_email",
        new=AsyncMock(return_value=admin),
    ):
        with pytest.raises(InvalidOtpError) as exc_info:
            await auth_service.verify_otp(VerifyOtpRequest(email="admin@example.com", otp="wrong"))
    assert exc_info.value.code == "E_400_AUTH_INVALID_OTP"


async def test_verify_otp_rejects_unknown_admin_without_revealing() -> None:
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_email",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(InvalidOtpError) as exc_info:
            await auth_service.verify_otp(VerifyOtpRequest(email="nope@example.com", otp="12345"))
    assert exc_info.value.code == "E_400_AUTH_INVALID_OTP"


async def test_verify_otp_rejects_expired() -> None:
    admin = _admin()
    row = PasswordResetOtp(
        email="admin@example.com",
        expires_at=utcnow() - timedelta(minutes=1),
        request_count=1,
        window_started_at=utcnow(),
    )
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=row)),
    ):
        with pytest.raises(InvalidOtpError):
            await auth_service.verify_otp(VerifyOtpRequest(email="admin@example.com", otp="12345"))


async def test_verify_otp_rejects_missing_row() -> None:
    admin = _admin()
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=None)),
    ):
        with pytest.raises(InvalidOtpError):
            await auth_service.verify_otp(VerifyOtpRequest(email="admin@example.com", otp="12345"))


async def test_update_password_rejects_unknown_admin_without_revealing() -> None:
    with patch.object(
        auth_service.auth_repository,
        "get_admin_by_email",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(PasswordResetFailedError) as exc_info:
            await auth_service.update_password(
                UpdatePasswordRequest(
                    email="nope@example.com",
                    new_password="S3cureP@ss",
                    confirm_password="S3cureP@ss",
                )
            )
    assert exc_info.value.code == "E_400_AUTH_PASSWORD_RESET_FAILED"


async def test_update_password_success_clears_lockout_and_session() -> None:
    admin = _admin(failed_login_attempts=4, locked_until=utcnow(), current_refresh_jti="r1")
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(
            auth_service.otp_repository,
            "get",
            new=AsyncMock(
                return_value=PasswordResetOtp(
                    email="admin@example.com",
                    expires_at=utcnow() + timedelta(minutes=5),
                    request_count=1,
                    window_started_at=utcnow(),
                    verified=True,
                )
            ),
        ),
        patch.object(
            auth_service.password_history_repository,
            "recent_for_admin",
            new=AsyncMock(return_value=[]),
        ),
        patch.object(auth_service, "verify_password", return_value=False),
        patch.object(auth_service, "hash_password", return_value="hashed"),
        patch.object(
            auth_service.password_history_repository,
            "add",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            auth_service.password_history_repository,
            "trim",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            auth_service.auth_repository,
            "update_admin_password",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(
            auth_service.otp_repository,
            "delete",
            new=AsyncMock(return_value=None),
        ) as delete_otp,
    ):
        result = await auth_service.update_password(
            UpdatePasswordRequest(
                email="admin@example.com",
                new_password="S3cureP@ss",
                confirm_password="S3cureP@ss",
            )
        )
    assert result is admin
    assert admin.failed_login_attempts == 0
    assert admin.locked_until is None
    assert admin.current_refresh_jti is None
    delete_otp.assert_awaited_once_with("admin@example.com")


async def test_update_password_rejects_reused_password() -> None:
    admin = _admin()
    entry = PasswordHistory(platform_admin_id=admin.id, hashed_password="oldhash")
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(
            auth_service.otp_repository,
            "get",
            new=AsyncMock(
                return_value=PasswordResetOtp(
                    email="admin@example.com",
                    expires_at=utcnow() + timedelta(minutes=5),
                    request_count=1,
                    window_started_at=utcnow(),
                    verified=True,
                )
            ),
        ),
        patch.object(
            auth_service.password_history_repository,
            "recent_for_admin",
            new=AsyncMock(return_value=[entry]),
        ),
        patch.object(auth_service, "verify_password", return_value=True),
    ):
        with pytest.raises(PasswordReuseError):
            await auth_service.update_password(
                UpdatePasswordRequest(
                    email="admin@example.com",
                    new_password="S3cureP@ss",
                    confirm_password="S3cureP@ss",
                )
            )


async def test_update_password_rejects_unverified_otp() -> None:
    admin = _admin()
    row = PasswordResetOtp(
        email="admin@example.com",
        expires_at=utcnow() + timedelta(minutes=5),
        request_count=1,
        window_started_at=utcnow(),
        verified=False,
    )
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=row)),
    ):
        with pytest.raises(PasswordResetFailedError) as exc_info:
            await auth_service.update_password(
                UpdatePasswordRequest(
                    email="admin@example.com",
                    new_password="S3cureP@ss",
                    confirm_password="S3cureP@ss",
                )
            )
    assert exc_info.value.code == "E_400_AUTH_PASSWORD_RESET_FAILED"


async def test_update_password_rejects_expired_otp() -> None:
    admin = _admin()
    row = PasswordResetOtp(
        email="admin@example.com",
        expires_at=utcnow() - timedelta(minutes=1),
        request_count=1,
        window_started_at=utcnow(),
        verified=True,
    )
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service.otp_repository, "get", new=AsyncMock(return_value=row)),
    ):
        with pytest.raises(PasswordResetFailedError) as exc_info:
            await auth_service.update_password(
                UpdatePasswordRequest(
                    email="admin@example.com",
                    new_password="S3cureP@ss",
                    confirm_password="S3cureP@ss",
                )
            )
    assert exc_info.value.code == "E_400_AUTH_PASSWORD_RESET_FAILED"


async def test_login_resets_expired_lockout() -> None:
    admin = _admin(failed_login_attempts=5, locked_until=utcnow() - timedelta(minutes=1))
    with (
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_email",
            new=AsyncMock(return_value=admin),
        ),
        patch.object(auth_service, "verify_password", return_value=True),
        patch.object(
            auth_service.rbac_service,
            "permissions_for_admin",
            new=AsyncMock(return_value={"S1.R"}),
        ),
        patch.object(
            auth_service.rbac_service,
            "roles_for_admin",
            new=AsyncMock(return_value={"super_admin"}),
        ),
        patch.object(auth_service, "create_access_token", return_value="access"),
        patch.object(auth_service, "create_refresh_token", return_value="refresh"),
        patch.object(auth_service, "decode_token", return_value={"jti": "r1"}),
        patch.object(
            auth_service.auth_repository,
            "save_admin",
            new=AsyncMock(return_value=admin),
        ),
    ):
        token = await auth_service.login(LoginRequest(email="admin@example.com", password="pw"))
    assert token.access_token == "access"
    assert admin.locked_until is None
    assert admin.failed_login_attempts == 0


async def test_logout_rejects_invalid_token() -> None:
    with patch.object(auth_service, "decode_token", side_effect=JWTError("bad token")):
        with pytest.raises(AuthenticationError):
            await auth_service.logout(access_token="bad-token")


async def test_logout_rejects_non_access_token() -> None:
    with patch.object(auth_service, "decode_token", return_value={"type": "refresh"}):
        with pytest.raises(AuthenticationError):
            await auth_service.logout(access_token="refresh-token")


async def test_logout_rejects_malformed_user_id() -> None:
    with patch.object(
        auth_service, "decode_token", return_value={"type": "access", "user_id": "not-a-uuid"}
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.logout(access_token="access-token")


async def test_logout_rejects_unknown_admin() -> None:
    with (
        patch.object(
            auth_service,
            "decode_token",
            return_value={"type": "access", "user_id": str(uuid.uuid4())},
        ),
        patch.object(
            auth_service.auth_repository,
            "get_admin_by_id",
            new=AsyncMock(return_value=None),
        ),
    ):
        with pytest.raises(AuthenticationError):
            await auth_service.logout(access_token="access-token")
