"""US00-TK19 — Health check estendido.

Remova o skip rodando:
"""

from fastapi.testclient import TestClient

from src.main import fastapi_app as app

client = TestClient(app, raise_server_exceptions=False)


def test_health_reports_dependencies_and_version():
    resp = client.get("/health")

    assert resp.status_code in (200, 503)
    body = resp.json()
    # status agregado
    assert body["status"] in ("ok", "degraded")
    # checagem por dependência
    assert "database" in body
    assert "mapbox" in body
    assert "firebase" in body
    # versão/commit
    assert "version" in body
    assert "commit" in body
