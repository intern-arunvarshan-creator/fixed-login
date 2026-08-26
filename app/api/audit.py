"""Audit recording: the ``@audit`` decorator and the request-context helper."""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from fastapi import Request
from pydantic import BaseModel

from app.exceptions.exceptions import AppError
from app.models.enums import ActorType, AuditAction, AuditResourceType
from app.models.platform_admin import PlatformAdmin
from app.services import audit_service

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class AuditContext:
    """Context passed to an ``@audit`` extractor (request, body, admin, result)."""

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
    actor_type: str | None = None,
) -> None:
    """Record an audit event with request-derived context (url, id, ip, user-agent)."""
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


def audit(
    action: AuditAction,
    resource_type: AuditResourceType | None = None,
    *,
    actor: ActorExtractor | None = None,
    resource_id: ResourceIdExtractor | None = None,
    details: DetailsExtractor | None = None,
    failure_action: AuditAction | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Record one Audit Entry per handler call, derived from its signature."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            ctx = _build_context(kwargs)
            actor_value = _resolve_actor(ctx, actor)
            actor_type = ActorType.ADMIN.value if actor_value is not None else None
            try:
                result = await func(*args, **kwargs)
            except AppError as exc:
                if failure_action is not None:
                    await _write_entry(
                        ctx=ctx,
                        actor=actor_value,
                        actor_type=actor_type,
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
                actor_type=actor_type,
                action=action,
                resource_type=resource_type,
                resource_id=_call(resource_id, ctx),
                details=_call(details, ctx),
                response=_dump_model(result),
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
    """Prefer the resolved admin's Login Email; fall back to the declared extractor."""
    if ctx.admin is not None:
        return ctx.admin.email
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
    actor_type: str | None = None,
) -> None:
    """Persist one Audit Entry, deriving request context and payload from ``ctx``."""
    await record_audit(
        request=ctx.request,
        actor=actor,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        payload=_dump_model(ctx.body, exclude_unset=True),
        response=response,
    )


def _inspect(args: dict[str, Any]) -> tuple[Request | None, Any, PlatformAdmin | None]:
    """Locate the request and body in args; the Current Admin is the ``admin`` parameter."""
    request: Request | None = None
    body: Any = None
    for value in args.values():
        if isinstance(value, Request):
            request = value
        elif isinstance(value, BaseModel):
            body = value
    admin = args.get("admin")
    if not isinstance(admin, PlatformAdmin):
        admin = None
    return request, body, admin


def _dump_model(value: Any, *, exclude_unset: bool = False) -> dict[str, Any] | None:
    """Serialize a pydantic model to a JSON-safe dict (``exclude_unset`` for request bodies)."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_unset=exclude_unset)
    return None
