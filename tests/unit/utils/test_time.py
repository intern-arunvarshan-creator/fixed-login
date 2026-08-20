"""Time helper tests."""

from app.utils.time import utcnow


def test_utcnow_is_naive_utc() -> None:
    now = utcnow()
    assert now.tzinfo is None
