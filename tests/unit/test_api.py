"""API layer tests (auth dependency + route smoke tests)."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_admin
from app.core.security import create_access_token
from app.exceptions.errors import ApiError
from app.models.platform_admin import PlatformAdmin


def test_get_current_admin_returns_admin() -> None:
    token = create_access_token("admin")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    db = AsyncMock()
    db.get = AsyncMock(return_value=PlatformAdmin(username="admin", hashed_password="hash"))

    admin = asyncio.run(get_current_admin(credentials, db))
    assert admin.username == "admin"


def test_get_current_admin_missing_credentials() -> None:
    db = AsyncMock()
    with pytest.raises(ApiError):
        asyncio.run(get_current_admin(None, db))


def test_health(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["code"] == "S_200_HEALTH_OK"


def test_protected_route_requires_token(client) -> None:
    resp = client.get("/api/v1/users")
    assert resp.status_code == 401
    assert resp.json()["code"] == "E_401_NOT_AUTHENTICATED"


def test_audit_logs_requires_token(client) -> None:
    resp = client.get("/api/v1/audit-logs")
    assert resp.status_code == 401
    assert resp.json()["code"] == "E_401_NOT_AUTHENTICATED"


def test_login_validation_error(client) -> None:
    resp = client.post("/api/v1/auth/login", json={"username": "admin"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "E_422_VALIDATION_FAILED"
    assert body["data"] is None


def test_login_rejects_invalid_username_format(client) -> None:
    resp = client.post(
        "/api/v1/auth/login", json={"username": "!@#$%admin-qw", "password": "Admin@123"}
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["data"] is None
    assert body["message"] == "Username must follow the valid format"


def test_create_user_validation_error_reports_affected_field(client) -> None:
    from app.api.deps import get_current_admin
    from app.main import app
    from app.models.platform_admin import PlatformAdmin

    app.dependency_overrides[get_current_admin] = lambda: PlatformAdmin(
        username="admin", hashed_password="hash"
    )
    try:
        resp = client.post(
            "/api/v1/users",
            json={"name": "Alice Smith", "email": "a@a.com", "password": "S3cureP@ss"},
        )
    finally:
        app.dependency_overrides.pop(get_current_admin, None)

    assert resp.status_code == 422
    body = resp.json()
    assert body["message"] == "Validation failed"
    assert body["data"]["errors"] == [
        {"field": "name", "issue": "Name must follow the valid format"}
    ]
