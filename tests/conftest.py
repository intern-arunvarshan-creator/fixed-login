import os
from unittest.mock import AsyncMock, MagicMock

import pytest

# Must run before any `app` import (pytest imports conftest first). Lets
# Settings() load in CI and fresh checkouts where there is no `.env`.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/platform_admin_v2"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests")


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.database.database import get_db
    from app.main import app

    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
