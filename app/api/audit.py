"""Request-derived audit context helper."""

from typing import Any

from fastapi import Request

from app.services import audit_service
from app.utils.redact import redact


async def record_audit(
    request: Request,
    actor: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    response: dict[str, Any] | None = None,
) -> None:
    """Record an audit event with request-derived context (url, id, ip, user-agent).

    ``payload``/``response`` should be JSON-safe dicts (e.g. via a pydantic
    model's ``model_dump(mode="json")``); credential-shaped fields are masked
    before the row is written.
    """
    await audit_service.record(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        url=request.url.path,
        payload=redact(payload),
        response=redact(response),
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
