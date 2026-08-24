"""Authentication and authorization dependencies (resolve the admin, check permissions)."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_token
from app.exceptions.errors import forbidden, not_authenticated
from app.models.enums import PermissionName
from app.models.platform_admin import PlatformAdmin
from app.services import auth_service, rbac_service

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


def require_permission(
    required: PermissionName,
) -> Callable[..., Awaitable[PlatformAdmin]]:
    """Build a dependency that allows the request only if the admin holds ``required``."""

    async def _dependency(
        admin: PlatformAdmin = Depends(get_current_admin),
    ) -> PlatformAdmin:
        granted = await rbac_service.permissions_for_admin(admin.id)
        if required.value not in granted:
            raise forbidden()
        return admin

    return _dependency
