from app.main import app
from fastapi.testclient import TestClient
import pytest


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_recovery_returns_strategies_and_recommendation(client: TestClient):
    response = client.post('/api/recovery/run', json={"scenario_id": "test", "budget": 10000})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert len(payload["strategies"]) >= 3
    assert payload["recommendation"]["recommended_action"]


def test_disruption_create_and_activate_flow(client: TestClient):
    create = client.post(
        '/api/disruptions',
        json={
            "type": "demand_shock",
            "name": "test-shock",
            "product_id": 1,
            "region_id": 1,
            "severity": 0.3,
            "start_date": "2026-01-01",
            "duration_days": 4,
            "demand_multiplier": 1.2,
            "delay_days": 0,
        },
    )
    assert create.status_code == 200
    created = create.json()
    assert created["active"] is False

    activate = client.post(f"/api/disruptions/{created['id']}/activate")
    assert activate.status_code == 200
    assert activate.json()["active"] is True
