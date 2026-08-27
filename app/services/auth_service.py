"""Auth business rules (login, token refresh, admin resolution)."""

import uuid
from datetime import UTC, datetime
from typing import Any

from jose import JWTError

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
    AuthenticationError,
    InvalidCredentialsError,
    InvalidOtpError,
    PasswordResetFailedError,
)
from app.models.enums import AdminStatus
from app.models.platform_admin import PlatformAdmin
from app.repositories import auth_repository, revoked_token_repository
from app.schemas.auth import (
    GenerateOtpRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UpdatePasswordRequest,
    VerifyOtpRequest,
)
from app.services import rbac_service

# Hardcoded until real OTP delivery (email/SMS) is wired up.
OTP_CODE = "12345"  # noqa: S105  # nosec B105  (fixed OTP, not a real secret)


@traced("auth_service.login")
async def login(credentials: LoginRequest) -> TokenResponse:
    admin = await auth_repository.get_admin_by_email(credentials.email)
    if admin is None or not verify_password(
        plain=credentials.password, hashed=admin.hashed_password
    ):
        raise InvalidCredentialsError()
    if admin.status != AdminStatus.ACTIVE:
        raise AccountInactiveError()
    permissions = await rbac_service.permissions_for_admin(admin.id)
    return await _issue_tokens(admin, permissions=sorted(permissions))


async def _issue_tokens(admin: PlatformAdmin, permissions: list[str]) -> TokenResponse:
    roles = sorted(await rbac_service.roles_for_admin(admin.id))
    subject = str(admin.id)
    refresh_token = create_refresh_token(subject)
    return TokenResponse(
        access_token=create_access_token(
            subject,
            refresh_token=refresh_token,
            permissions=permissions,
            email=admin.email,
            username=admin.username,
            roles=roles,
        ),
        refresh_token=refresh_token,
    )


async def get_admin_by_id(admin_id: uuid.UUID) -> PlatformAdmin:
    admin = await auth_repository.get_admin_by_id(admin_id)
    if admin is None:
        raise AuthenticationError()
    if admin.status != AdminStatus.ACTIVE:
        raise AccountInactiveError()
    return admin


async def get_admin_from_payload(payload: dict[str, Any]) -> PlatformAdmin:
    """Resolve and validate the admin behind a decoded access/refresh token payload."""
    jti = payload.get("jti")
    if jti is not None and await revoked_token_repository.is_revoked(jti):
        raise AuthenticationError()
    try:
        admin_id = uuid.UUID(str(payload.get("user_id")))
    except ValueError:
        raise AuthenticationError() from None
    return await get_admin_by_id(admin_id)


async def refresh(payload: RefreshRequest) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise AuthenticationError() from None
    if data.get("type") != "refresh":
        raise AuthenticationError()
    admin = await get_admin_from_payload(data)
    permissions = await rbac_service.permissions_for_admin(admin.id)
    return await _issue_tokens(admin, permissions=sorted(permissions))


def _epoch_to_naive_utc(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=UTC).replace(tzinfo=None)


@traced("auth_service.logout")
async def logout(access_token: str) -> None:
    """Revoke the access token and its linked refresh token so neither works again."""
    try:
        payload = decode_token(access_token)
    except JWTError:
        raise AuthenticationError() from None
    if payload.get("type") != "access":
        raise AuthenticationError()
    access_jti = payload.get("jti")
    access_exp = payload.get("exp")
    if not access_jti or access_exp is None:
        raise AuthenticationError()
    await revoked_token_repository.revoke(
        jti=access_jti, expires_at=_epoch_to_naive_utc(access_exp)
    )

    refresh_jti = payload.get("rjti")
    refresh_exp = payload.get("rexp")
    if refresh_jti and refresh_exp is not None:
        await revoked_token_repository.revoke(
            jti=refresh_jti, expires_at=_epoch_to_naive_utc(refresh_exp)
        )


@traced("auth_service.generate_otp")
async def generate_otp(payload: GenerateOtpRequest) -> None:
    """Request an OTP, returning normally for unknown/inactive accounts to avoid enumeration."""
    admin = await auth_repository.get_admin_by_email(payload.email)
    if admin is None or admin.status != AdminStatus.ACTIVE:
        return


@traced("auth_service.verify_otp")
async def verify_otp(payload: VerifyOtpRequest) -> None:
    """Verify the OTP, returning one opaque failure for any invalid case."""
    admin = await auth_repository.get_admin_by_email(payload.email)
    if admin is None or admin.status != AdminStatus.ACTIVE or payload.otp != OTP_CODE:
        raise InvalidOtpError()


@traced("auth_service.update_password")
async def update_password(payload: UpdatePasswordRequest) -> PlatformAdmin:
    """Set a new password, failing opaquely for unknown or inactive accounts."""
    admin = await auth_repository.get_admin_by_email(payload.email)
    if admin is None or admin.status != AdminStatus.ACTIVE:
        raise PasswordResetFailedError()
    return await auth_repository.update_admin_password(
        admin=admin, hashed_password=hash_password(payload.new_password)
    )
