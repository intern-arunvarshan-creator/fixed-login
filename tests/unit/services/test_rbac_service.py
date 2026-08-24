"""RBAC service tests (repositories mocked)."""

import uuid
from unittest.mock import AsyncMock, patch

from app.services import rbac_service


async def test_permissions_for_admin() -> None:
    admin_id = uuid.uuid4()
    with patch.object(
        rbac_service.rbac_repository,
        "permission_names_for_admin",
        new=AsyncMock(return_value={"user.read"}),
    ):
        result = await rbac_service.permissions_for_admin(admin_id)
    assert result == {"user.read"}
