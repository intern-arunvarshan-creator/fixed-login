"""Users route smoke tests."""


def test_protected_route_requires_token(client) -> None:
    resp = client.get("/api/v1/users")
    assert resp.status_code == 401
    assert resp.json()["code"] == "E_401_NOT_AUTHENTICATED"
