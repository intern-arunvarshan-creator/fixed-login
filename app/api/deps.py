import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database.database import get_db
from app.exceptions.errors import not_authenticated
from app.models.platform_admin import PlatformAdmin

bearer_scheme = HTTPBearer(auto_error=False)


def _admin_id_from(credentials: HTTPAuthorizationCredentials | None) -> uuid.UUID:
    if credentials is None:
        raise not_authenticated()
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise not_authenticated() from None
    if payload.get("type") != "access":
        raise not_authenticated()
    subject = payload.get("sub")
    if not subject:
        raise not_authenticated()
    try:
        return uuid.UUID(str(subject))
    except ValueError:
        raise not_authenticated() from None


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> PlatformAdmin:
    admin = await db.get(PlatformAdmin, _admin_id_from(credentials))
    if admin is None:
        raise not_authenticated()
    return admin
