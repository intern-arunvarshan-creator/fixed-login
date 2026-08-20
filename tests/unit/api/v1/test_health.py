"""Health route smoke tests."""


def test_health(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["code"] == "S_200_HEALTH_OK"
