from fastapi.testclient import TestClient

from reorder.api.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})


def test_health_is_not_versioned() -> None:
    assert client.get("/api/v1/health").status_code == 404
