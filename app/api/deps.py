"""Authentication dependency: resolve the current admin from the bearer token."""

from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_token
from app.exceptions.errors import not_authenticated
from app.models.platform_admin import PlatformAdmin
from app.services import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


def _access_token_payload(credentials: HTTPAuthorizationCredentials | None) -> dict[str, Any]:
    if credentials is None:
        raise not_authenticated()
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise not_authenticated() from None
    if payload.get("type") != "access":
        raise not_authenticated()
    return payload


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> PlatformAdmin:
    return await auth_service.get_admin_from_payload(_access_token_payload(credentials))
