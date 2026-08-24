"""Mask credential-shaped fields before they're persisted to the audit trail."""

from typing import Any

_REDACTED = "***"
_SENSITIVE_KEYS = {
    "password",
    "new_password",
    "confirm_password",
    "hashed_password",
    "access_token",
    "refresh_token",
    "otp",
}


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _redact_dict(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def _redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {
        k: (_REDACTED if k in _SENSITIVE_KEYS else _redact_value(v)) for k, v in data.items()
    }


def redact(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Recursively mask credential-shaped keys anywhere in the (JSON-safe) structure."""
    if data is None:
        return None
    return _redact_dict(data)
