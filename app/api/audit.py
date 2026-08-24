"""Audit recording: the ``@audit`` decorator and the request-context helper."""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from fastapi import Request
from pydantic import BaseModel

from app.exceptions.errors import ApiError
from app.models.enums import AuditAction, AuditResourceType
from app.models.platform_admin import PlatformAdmin
from app.services import audit_service
from app.utils.redact import redact

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class AuditContext:
    """Values an ``@audit`` extractor can read.

    ``body`` and ``result`` are ``Any`` because they are endpoint-specific DTOs
    (the request body model and the handler's return value); each extractor knows
    the concrete types of its own endpoint.
    """

    request: Request
    args: dict[str, Any]
    body: Any
    admin: PlatformAdmin | None
    result: Any


ActorExtractor = Callable[[AuditContext], str | None]
ResourceIdExtractor = Callable[[AuditContext], str | None]
DetailsExtractor = Callable[[AuditContext], dict[str, Any] | None]


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
    """Record an audit event with request-derived context (url, id, ip, user-agent)."""
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


def audit(
    action: AuditAction,
    resource_type: AuditResourceType | None = None,
    *,
    actor: ActorExtractor | None = None,
    resource_id: ResourceIdExtractor | None = None,
    details: DetailsExtractor | None = None,
    failure_action: AuditAction | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Record one Audit Entry per handler call, deriving context from intent.

    Auto-derived: ``actor`` (from a ``PlatformAdmin`` argument), request context,
    ``payload`` (the request body model), and ``response`` (the return value).
    ``resource_id`` and ``details`` are post-hoc/domain-specific, so they are
    extractor callables. On an ``ApiError`` a second entry is recorded using
    ``failure_action`` (when set) before the error is re-raised.
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            ctx = _build_context(kwargs)
            actor_value = _resolve_actor(ctx, actor)
            try:
                result = await func(*args, **kwargs)
            except ApiError as exc:
                if failure_action is not None:
                    await _write_entry(
                        ctx=ctx,
                        actor=actor_value,
                        action=failure_action,
                        resource_type=resource_type,
                        resource_id=_call(resource_id, ctx),
                        details={"error_code": exc.code},
                    )
                raise
            ctx.result = result
            await _write_entry(
                ctx=ctx,
                actor=actor_value,
                action=action,
                resource_type=resource_type,
                resource_id=_call(resource_id, ctx),
                details=_call(details, ctx),
                response=_dump_response(result),
            )
            return result

        return wrapper

    return decorator


def _build_context(kwargs: Mapping[str, Any]) -> AuditContext:
    """Assemble the request, body, and admin from the handler's resolved arguments."""
    resolved = dict(kwargs)
    request, body, admin = _inspect(resolved)
    if request is None:
        raise RuntimeError("@audit requires the endpoint to declare `request: Request`")
    return AuditContext(request=request, args=resolved, body=body, admin=admin, result=None)


def _resolve_actor(ctx: AuditContext, actor: ActorExtractor | None) -> str | None:
    """Prefer the resolved admin's username; fall back to the declared extractor."""
    if ctx.admin is not None:
        return ctx.admin.username
    return _call(actor, ctx)


def _call[T](
    extractor: Callable[[AuditContext], T] | None,
    ctx: AuditContext,
) -> T | None:
    """Invoke an optional extractor, or return ``None`` when none is declared."""
    if extractor is None:
        return None
    return extractor(ctx)


async def _write_entry(
    ctx: AuditContext,
    *,
    actor: str | None,
    action: AuditAction,
    resource_type: AuditResourceType | None,
    resource_id: str | None,
    details: dict[str, Any] | None,
    response: dict[str, Any] | None = None,
) -> None:
    """Persist one Audit Entry, deriving request context and payload from ``ctx``."""
    await record_audit(
        request=ctx.request,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        payload=_dump_body(ctx.body),
        response=response,
    )


def _inspect(args: dict[str, Any]) -> tuple[Request | None, Any, PlatformAdmin | None]:
    """Find the Request, body model, and PlatformAdmin among resolved arguments."""
    request: Request | None = None
    body: Any = None
    admin: PlatformAdmin | None = None
    for value in args.values():
        if isinstance(value, Request):
            request = value
        elif isinstance(value, PlatformAdmin):
            admin = value
        elif isinstance(value, BaseModel):
            body = value
    return request, body, admin


def _dump_body(body: Any) -> dict[str, Any] | None:
    """Serialize the request body model, capturing only fields the client sent."""
    if isinstance(body, BaseModel):
        return body.model_dump(mode="json", exclude_unset=True)
    return None


def _dump_response(result: Any) -> dict[str, Any] | None:
    """Serialize the handler's return value if it is a pydantic model."""
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    return None
