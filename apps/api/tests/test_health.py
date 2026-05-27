"""Step 3 smoke test — verify the FastAPI app boots and /health returns 200."""

from fastapi.testclient import TestClient

from src.main import app


def test_health_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "TICDSS API"
    assert payload["version"] == "0.1.0"
