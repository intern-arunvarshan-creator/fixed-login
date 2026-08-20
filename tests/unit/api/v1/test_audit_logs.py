"""Audit logs route smoke tests."""


def test_audit_logs_requires_token(client) -> None:
    resp = client.get("/api/v1/audit-logs")
    assert resp.status_code == 401
    assert resp.json()["code"] == "E_401_NOT_AUTHENTICATED"
