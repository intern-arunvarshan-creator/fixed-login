"""Auth route smoke tests."""


def test_login_validation_error(client) -> None:
    resp = client.post("/api/v1/auth/login", json={"username": "admin"})
    assert resp.status_code == 422
    assert resp.json()["code"] == "E_422_VALIDATION_FAILED"
