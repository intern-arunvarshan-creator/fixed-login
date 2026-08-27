"""Auth business rules (login, token refresh, admin resolution)."""

import uuid
from datetime import timedelta
from typing import Any

from jose import JWTError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.tracing import traced
from app.exceptions.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    AuthenticationError,
    InvalidCredentialsError,
    InvalidOtpError,
    OtpThrottledError,
    PasswordResetFailedError,
    PasswordReuseError,
)
from app.models.enums import Status
from app.models.password_reset_otp import PasswordResetOtp
from app.models.platform_admin import PlatformAdmin
from app.repositories import (
    auth_repository,
    otp_repository,
    password_history_repository,
)
from app.schemas.auth import (
    GenerateOtpRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UpdatePasswordRequest,
    VerifyOtpRequest,
)
from app.services import rbac_service
from app.utils.time import utcnow

# Hardcoded until real OTP delivery (email/SMS) is wired up.
OTP_CODE = "12345"  # noqa: S105  # nosec B105  (fixed OTP, not a real secret)


@traced("auth_service.login")
async def login(credentials: LoginRequest) -> TokenResponse:
    admin = await auth_repository.get_admin_by_email(credentials.email)
    if admin is None:
        raise InvalidCredentialsError()
    now = utcnow()
    if admin.locked_until is not None:
        if admin.locked_until > now:
            raise AccountLockedError()
        admin.locked_until = None
        admin.failed_login_attempts = 0
    if not verify_password(plain=credentials.password, hashed=admin.hashed_password):
        admin.failed_login_attempts += 1
        if admin.failed_login_attempts >= settings.max_failed_login_attempts:
            admin.locked_until = now + timedelta(minutes=settings.lockout_minutes)
            admin.failed_login_attempts = 0
            await auth_repository.save_admin(admin)
            raise AccountLockedError()
        await auth_repository.save_admin(admin)
        raise InvalidCredentialsError()
    if admin.status != Status.ACTIVE:
        raise AccountInactiveError()
    admin.failed_login_attempts = 0
    admin.locked_until = None
    permissions = await rbac_service.permissions_for_admin(admin.id)
    return await _issue_session(admin, permissions=sorted(permissions))


async def _issue_session(admin: PlatformAdmin, permissions: list[str]) -> TokenResponse:
    token, refresh_jti = await _issue_tokens(admin, permissions)
    admin.current_refresh_jti = refresh_jti
    await auth_repository.save_admin(admin)
    return token


async def _issue_tokens(admin: PlatformAdmin, permissions: list[str]) -> tuple[TokenResponse, str]:
    roles = sorted(await rbac_service.roles_for_admin(admin.id))
    subject = str(admin.id)
    refresh_token = create_refresh_token(subject)
    refresh_jti = str(decode_token(refresh_token)["jti"])
    return (
        TokenResponse(
            access_token=create_access_token(
                subject,
                refresh_token,
                permissions,
                email=admin.email,
                username=admin.username,
                roles=roles,
            ),
            refresh_token=refresh_token,
        ),
        refresh_jti,
    )


async def get_admin_by_id(admin_id: uuid.UUID) -> PlatformAdmin:
    admin = await auth_repository.get_admin_by_id(admin_id)
    if admin is None:
        raise AuthenticationError()
    if admin.status != Status.ACTIVE:
        raise AccountInactiveError()
    return admin


async def get_admin_from_payload(payload: dict[str, Any]) -> PlatformAdmin:
    """Resolve and validate the admin behind a decoded access/refresh token payload."""
    try:
        admin_id = uuid.UUID(str(payload.get("user_id")))
    except ValueError:
        raise AuthenticationError() from None
    admin = await get_admin_by_id(admin_id)
    _require_current_session(admin, payload)
    return admin


def _require_current_session(admin: PlatformAdmin, payload: dict[str, Any]) -> None:
    """Reject tokens that don't belong to the admin's current session."""
    current = admin.current_refresh_jti
    kind = payload.get("type")
    if current is None or kind not in {"access", "refresh"}:
        raise AuthenticationError()
    presented = payload.get("rjti") if kind == "access" else payload.get("jti")
    if presented != current:
        raise AuthenticationError()


async def refresh(payload: RefreshRequest) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise AuthenticationError() from None
    if data.get("type") != "refresh":
        raise AuthenticationError()
    admin = await get_admin_from_payload(data)
    permissions = await rbac_service.permissions_for_admin(admin.id)
    return await _issue_session(admin, permissions=sorted(permissions))


@traced("auth_service.logout")
async def logout(access_token: str) -> None:
    """End the current session so neither the access nor refresh token works again."""
    try:
        payload = decode_token(access_token)
    except JWTError:
        raise AuthenticationError() from None
    if payload.get("type") != "access":
        raise AuthenticationError()
    await _clear_current_session(payload)


async def _clear_current_session(payload: dict[str, Any]) -> None:
    """Clear the current-session pointer so no token for this admin validates."""
    try:
        admin_id = uuid.UUID(str(payload.get("user_id")))
    except ValueError:
        raise AuthenticationError() from None
    admin = await auth_repository.get_admin_by_id(admin_id)
    if admin is None:
        raise AuthenticationError()
    admin.current_refresh_jti = None
    await auth_repository.save_admin(admin)


@traced("auth_service.generate_otp")
async def generate_otp(payload: GenerateOtpRequest) -> None:
    """Request an OTP, returning normally for unknown/inactive accounts to avoid enumeration."""
    admin = await auth_repository.get_admin_by_email(payload.email)
    if admin is None or admin.status != Status.ACTIVE:
        return
    now = utcnow()
    row = await otp_repository.get(payload.email)
    expiry = now + timedelta(minutes=settings.otp_expiry_minutes)
    window = timedelta(minutes=settings.otp_throttle_window_minutes)
    if row is None:
        await otp_repository.save(
            PasswordResetOtp(
                email=payload.email,
                expires_at=expiry,
                request_count=1,
                window_started_at=now,
                verified=False,
            )
        )
    elif now >= row.window_started_at + window:
        row.expires_at = expiry
        row.request_count = 1
        row.window_started_at = now
        row.verified = False
        await otp_repository.save(row)
    elif row.request_count >= settings.otp_max_requests_per_window:
        raise OtpThrottledError()
    else:
        row.request_count += 1
        row.expires_at = expiry
        row.verified = False
        await otp_repository.save(row)


@traced("auth_service.verify_otp")
async def verify_otp(payload: VerifyOtpRequest) -> None:
    """Verify the OTP, returning one opaque failure for any invalid case."""
    admin = await auth_repository.get_admin_by_email(payload.email)
    if admin is None or admin.status != Status.ACTIVE or payload.otp != OTP_CODE:
        raise InvalidOtpError()
    row = await otp_repository.get(payload.email)
    if row is None or utcnow() >= row.expires_at:
        raise InvalidOtpError()
    row.verified = True
    await otp_repository.save(row)


@traced("auth_service.update_password")
async def update_password(payload: UpdatePasswordRequest) -> PlatformAdmin:
    """Set a new password, failing opaquely for unknown or inactive accounts."""
    admin = await auth_repository.get_admin_by_email(payload.email)
    if admin is None or admin.status != Status.ACTIVE:
        raise PasswordResetFailedError()
    row = await otp_repository.get(payload.email)
    if row is None or not row.verified or utcnow() >= row.expires_at:
        raise PasswordResetFailedError()
    recent = await password_history_repository.recent_for_admin(
        admin.id, settings.password_history_depth
    )
    if verify_password(payload.new_password, admin.hashed_password) or any(
        verify_password(payload.new_password, entry.hashed_password) for entry in recent
    ):
        raise PasswordReuseError()
    await password_history_repository.add(admin.id, admin.hashed_password, utcnow())
    await password_history_repository.trim(admin.id, settings.password_history_depth)
    admin.failed_login_attempts = 0
    admin.locked_until = None
    admin.current_refresh_jti = None
    updated = await auth_repository.update_admin_password(
        admin=admin, hashed_password=hash_password(payload.new_password)
    )
    await otp_repository.delete(payload.email)
    return updated
