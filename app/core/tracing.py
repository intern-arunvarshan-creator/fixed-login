import atexit
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from app.core.config import settings

logger = logging.getLogger("app.core.tracing")

_configured = False


def _normalize_otlp_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.path in ("", "/"):
        return urlunparse(parsed._replace(path="/v1/traces"))
    return endpoint


def get_tracer() -> trace.Tracer:
    return trace.get_tracer(settings.tracing_service_name)


def configure_tracing() -> None:
    """Idempotent. Must run *before* the first SQLAlchemy engine is created."""
    global _configured
    if _configured or not settings.tracing_enabled:
        return

    provider = TracerProvider(
        resource=Resource.create({"service.name": settings.tracing_service_name}),
        sampler=ParentBased(TraceIdRatioBased(settings.tracing_sample_rate)),
    )
    exporter = (
        OTLPSpanExporter(endpoint=_normalize_otlp_endpoint(settings.tracing_otlp_endpoint))
        if settings.tracing_otlp_endpoint
        else ConsoleSpanExporter()
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    SQLAlchemyInstrumentor().instrument()
    _configured = True


def instrument_app(app: FastAPI) -> None:
    """Instrument a FastAPI app's HTTP layer (call once the app exists)."""
    if settings.tracing_enabled:
        FastAPIInstrumentor.instrument_app(app, exclude_spans=["receive", "send"])


P = ParamSpec("P")
R = TypeVar("R")


def traced(name: str) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator that wraps an async function in a span named ``name``."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with get_tracer().start_as_current_span(name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def _shutdown() -> None:
    if _configured:
        trace.get_tracer_provider().shutdown()


atexit.register(_shutdown)
