"""Auth repository tests (mocked async session)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.repositories import auth_repository


def test_get_admin_by_username() -> None:
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalar_one_or_none.return_value = "admin-object"
    assert asyncio.run(auth_repository.get_admin_by_username(db, "admin")) == "admin-object"
