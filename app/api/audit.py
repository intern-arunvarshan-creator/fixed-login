"""Audit recording helper shared by API endpoints and auth dependencies."""

from typing import Any

from fastapi import Request

from app.services import audit_service


async def record_audit(
    request: Request,
    actor: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    response: dict[str, Any] | None = None,
    actor_type: str | None = None,
) -> None:
    """Record one Audit Entry, deriving URL, IP and user-agent from ``request``."""
    await audit_service.record(
        action=action,
        actor=actor,
        actor_type=actor_type,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        url=request.url.path,
        payload=payload,
        response=response,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
