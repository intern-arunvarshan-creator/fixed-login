import uuid

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.core.tracing import traced
from app.exceptions.errors import account_inactive, invalid_credentials, not_authenticated
from app.models.enums import AdminStatus
from app.repositories import auth_repository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse


@traced("auth_service.login")
async def login(db: AsyncSession, credentials: LoginRequest) -> TokenResponse:
    admin = await auth_repository.get_admin_by_email(db, credentials.email)
    if admin is None or not verify_password(credentials.password, admin.hashed_password):
        raise invalid_credentials()
    if admin.status != AdminStatus.ACTIVE:
        raise account_inactive()
    return TokenResponse(
        access_token=create_access_token(str(admin.id)),
        refresh_token=create_refresh_token(str(admin.id)),
    )


async def refresh(db: AsyncSession, payload: RefreshRequest) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise not_authenticated() from None
    if data.get("type") != "refresh":
        raise not_authenticated()
    admin = None
    try:
        admin_id = uuid.UUID(str(data.get("sub")))
    except ValueError:
        admin_id = None
    if admin_id is not None:
        admin = await auth_repository.get_admin_by_id(db, admin_id)
    if admin is None:
        raise not_authenticated()
    return TokenResponse(
        access_token=create_access_token(str(admin.id)),
        refresh_token=create_refresh_token(str(admin.id)),
    )
