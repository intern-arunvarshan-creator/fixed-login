"""Ambient audit-actor context (set at the boundary, read by the service layer).

The actor is a property of the request, not of the business operation, so it
travels in a ContextVar rather than through service signatures (ADR-0014).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass

from app.models.enums import ActorType


@dataclass(frozen=True)
class AuditActor:
    """The actor (snapshot string + type) behind an action."""

    actor: str
    actor_type: str


current_actor: ContextVar[AuditActor | None] = ContextVar("audit_actor", default=None)


def set_current_actor(actor: str, actor_type: str) -> Token[AuditActor | None]:
    return current_actor.set(AuditActor(actor=actor, actor_type=actor_type))


def reset_current_actor(token: Token[AuditActor | None]) -> None:
    current_actor.reset(token)


def get_current_actor() -> AuditActor | None:
    return current_actor.get()


@asynccontextmanager
async def system_actor(name: str) -> AsyncIterator[None]:
    """Run a block with the actor set to an automation identity (non-HTTP entry points)."""
    token = set_current_actor(name, ActorType.SYSTEM.value)
    try:
        yield
    finally:
        reset_current_actor(token)
