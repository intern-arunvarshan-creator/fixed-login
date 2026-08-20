"""PlatformAdmin model tests."""

from app.models.platform_admin import PlatformAdmin


def test_platform_admin_fields() -> None:
    admin = PlatformAdmin(username="admin", hashed_password="hash")
    assert admin.username == "admin"
