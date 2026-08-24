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
from app.exceptions.errors import (
    account_inactive,
    admin_not_found,
    invalid_credentials,
    invalid_otp,
    not_authenticated,
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

# Hardcoded until real OTP delivery (email/SMS) is wired up.
OTP_CODE = "12345"  # noqa: S105  # nosec B105  (fixed OTP, not a real secret)


@traced("auth_service.login")
async def login(credentials: LoginRequest) -> TokenResponse:
    admin = await auth_repository.get_admin_by_email(credentials.email)
    if admin is None or not verify_password(
        plain=credentials.password, hashed=admin.hashed_password
    ):
        raise invalid_credentials()
    if admin.status != AdminStatus.ACTIVE:
        raise account_inactive()
    return _issue_tokens(str(admin.id))


def _issue_tokens(subject: str) -> TokenResponse:
    refresh_token = create_refresh_token(subject)
    return TokenResponse(
        access_token=create_access_token(subject, refresh_token=refresh_token),
        refresh_token=refresh_token,
    )


async def get_admin_by_id(admin_id: uuid.UUID) -> PlatformAdmin:
    admin = await auth_repository.get_admin_by_id(admin_id)
    if admin is None:
        raise not_authenticated()
    return admin


async def get_admin_from_payload(payload: dict[str, Any]) -> PlatformAdmin:
    """Resolve and validate the admin behind a decoded access/refresh token payload."""
    jti = payload.get("jti")
    if jti is not None and await revoked_token_repository.is_revoked(jti):
        raise not_authenticated()
    try:
        admin_id = uuid.UUID(str(payload.get("sub")))
    except ValueError:
        raise not_authenticated() from None
    return await get_admin_by_id(admin_id)


async def refresh(payload: RefreshRequest) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise not_authenticated() from None
    if data.get("type") != "refresh":
        raise not_authenticated()
    admin = await get_admin_from_payload(data)
    return _issue_tokens(str(admin.id))


def _epoch_to_naive_utc(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=UTC).replace(tzinfo=None)


@traced("auth_service.logout")
async def logout(access_token: str) -> None:
    """Revoke the access token and its linked refresh token so neither works again."""
    try:
        payload = decode_token(access_token)
    except JWTError:
        raise not_authenticated() from None
    if payload.get("type") != "access":
        raise not_authenticated()
    access_jti = payload.get("jti")
    access_exp = payload.get("exp")
    if not access_jti or access_exp is None:
        raise not_authenticated()
    await revoked_token_repository.revoke(
        jti=access_jti, expires_at=_epoch_to_naive_utc(access_exp)
    )

    refresh_jti = payload.get("rjti")
    refresh_exp = payload.get("rexp")
    if refresh_jti and refresh_exp is not None:
        await revoked_token_repository.revoke(
            jti=refresh_jti, expires_at=_epoch_to_naive_utc(refresh_exp)
        )


async def _get_active_admin_by_email(email: str) -> PlatformAdmin:
    admin = await auth_repository.get_admin_by_email(email)
    if admin is None:
        raise admin_not_found()
    if admin.status != AdminStatus.ACTIVE:
        raise account_inactive()
    return admin


@traced("auth_service.generate_otp")
async def generate_otp(payload: GenerateOtpRequest) -> None:
    await _get_active_admin_by_email(payload.email)


@traced("auth_service.verify_otp")
async def verify_otp(payload: VerifyOtpRequest) -> None:
    await _get_active_admin_by_email(payload.email)
    if payload.otp != OTP_CODE:
        raise invalid_otp()


@traced("auth_service.update_password")
async def update_password(payload: UpdatePasswordRequest) -> PlatformAdmin:
    admin = await _get_active_admin_by_email(payload.email)
    return await auth_repository.update_admin_password(
        admin=admin, hashed_password=hash_password(payload.new_password)
    )
