"""User model tests."""

from app.models.enums import UserStatus
from app.models.user import User


def test_user_defaults() -> None:
    user = User(name="Alice", email="alice@example.com", hashed_password="hash")
    assert user.status is UserStatus.ACTIVE
    assert user.id is not None
    assert user.created_at is not None
