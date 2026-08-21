"""Auth schema (DTO) tests."""

from app.schemas.auth import LoginRequest, TokenResponse


def test_login_request() -> None:
    assert LoginRequest(email="admin@example.com", password="pw").email == "admin@example.com"


def test_token_response_defaults() -> None:
    assert TokenResponse(access_token="a", refresh_token="r").token_type == "bearer"
