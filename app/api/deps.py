"""Authentication and authorization dependencies (resolve the admin, check permissions)."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.api.audit import record_audit
from app.core.security import decode_token
from app.exceptions.errors import forbidden, not_authenticated
from app.models.enums import AuditAction, AuditResourceType, PermissionName
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
) -> Callable[..., Awaitable[None]]:
    """Build a guard that allows the request only if the admin holds ``required``.

    Returns ``None``: this is an authorization gate, not an identity provider.
    Identity comes from ``get_current_admin``, which routes declare explicitly
    whenever they need the Current Admin (e.g. for the audit actor).
    """

    async def _dependency(
        request: Request,
        admin: PlatformAdmin = Depends(get_current_admin),
    ) -> None:
        granted = await rbac_service.permissions_for_admin(admin.id)
        if required.value not in granted:
            await _record_denial(request=request, admin=admin, permission=required)
            raise forbidden()
        return None

    return _dependency


async def _record_denial(
    request: Request,
    admin: PlatformAdmin,
    permission: PermissionName,
) -> None:
    """Record an ``access.denied`` Audit Entry before the 403 is raised."""
    await record_audit(
        request=request,
        actor=admin.email,
        action=AuditAction.ACCESS_DENIED,
        resource_type=_denial_resource_type(permission),
        details={
            "permission": permission.value,
            "display_name": admin.username,
            "method": request.method,
            "path": request.url.path,
        },
    )


def _denial_resource_type(permission: PermissionName) -> AuditResourceType | None:
    """Map a permission's resource prefix (e.g. ``user``) to its resource type."""
    try:
        return AuditResourceType(permission.value.split(".", 1)[0])
    except ValueError:
        return None
