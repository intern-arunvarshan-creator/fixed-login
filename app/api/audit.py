from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import audit_service


async def record_audit(
    db: AsyncSession,
    request: Request,
    *,
    actor: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Record an audit event with request-derived context (id, ip, user-agent)."""
    await audit_service.record(
        db,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
