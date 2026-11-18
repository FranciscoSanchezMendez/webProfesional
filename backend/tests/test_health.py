import pytest
from fastapi.testclient import TestClient

from app.api.v1 import health
from app.main import app

client = TestClient(app)


def test_liveness_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_ok_when_database_responds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "check_database", lambda _url: True)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_readiness_503_when_database_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "check_database", lambda _url: False)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
