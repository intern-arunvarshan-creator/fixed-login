import contextvars
import json
import logging
import sys
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from opentelemetry import trace

from app.core.config import settings

# Request-scoped correlation id; set/cleared by RequestContextMiddleware.
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

_STRUCTURED_FIELDS = (
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client_ip",
    "user_agent",
    "actor",
    "action",
    "resource_type",
    "resource_id",
)


class RequestIdFilter(logging.Filter):
    """Attach the current request_id (if any) to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        span_ctx = trace.get_current_span().get_span_context()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "trace_id": format(span_ctx.trace_id, "032x") if span_ctx.is_valid else None,
            "span_id": format(span_ctx.span_id, "016x") if span_ctx.is_valid else None,
        }
        for field in _STRUCTURED_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the root logger for structured JSON output. Idempotent."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(settings.log_level.upper())

    if settings.log_to_console:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(JsonFormatter())
        console.addFilter(RequestIdFilter())
        root.addHandler(console)

    if settings.log_to_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(JsonFormatter())
        file_handler.addFilter(RequestIdFilter())
        root.addHandler(file_handler)
