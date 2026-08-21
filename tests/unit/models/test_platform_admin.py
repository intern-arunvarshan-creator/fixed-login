"""PlatformAdmin model tests."""

from app.models.enums import AdminStatus
from app.models.platform_admin import PlatformAdmin


def test_platform_admin_fields() -> None:
    admin = PlatformAdmin(username="admin", email="admin@example.com", hashed_password="hash")
    assert admin.username == "admin"
    assert admin.email == "admin@example.com"
    assert admin.status == AdminStatus.ACTIVE
