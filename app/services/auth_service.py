from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.core.tracing import traced
from app.exceptions.errors import invalid_credentials, not_authenticated
from app.repositories import auth_repository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse


@traced("auth_service.login")
async def login(db: AsyncSession, credentials: LoginRequest) -> TokenResponse:
    admin = await auth_repository.get_admin_by_username(db, credentials.username)
    if admin is None or not verify_password(credentials.password, admin.hashed_password):
        raise invalid_credentials()
    return TokenResponse(
        access_token=create_access_token(admin.username),
        refresh_token=create_refresh_token(admin.username),
    )


async def refresh(db: AsyncSession, payload: RefreshRequest) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise not_authenticated() from None
    if data.get("type") != "refresh":
        raise not_authenticated()
    username = data.get("sub")
    admin = await auth_repository.get_admin_by_username(db, str(username))
    if admin is None:
        raise not_authenticated()
    return TokenResponse(
        access_token=create_access_token(admin.username),
        refresh_token=create_refresh_token(admin.username),
    )
