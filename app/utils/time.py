from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC now (matches PostgreSQL ``timestamp without time zone``)."""
    return datetime.now(UTC).replace(tzinfo=None)
