from datetime import UTC, datetime

from fastapi.testclient import TestClient


def alert_payload(**overrides):
    payload = {
        "alert_name": "HighErrorRate",
        "service_name": "checkout-api",
        "environment": "production",
        "severity": "critical",
        "status": "firing",
        "started_at": "2026-07-02T12:00:00Z",
        "payload": {"error_rate": 0.35},
    }
    payload.update(overrides)
    return payload


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_alert_ingestion_deduplicates_active_incident(client: TestClient) -> None:
    first = client.post("/api/v1/alerts", json=alert_payload())
    second = client.post(
        "/api/v1/alerts",
        json=alert_payload(started_at="2026-07-02T12:05:00Z", payload={"error_rate": 0.42}),
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["incident_id"] == second.json()["incident_id"]

    incidents = client.get("/api/v1/incidents").json()
    assert len(incidents) == 1
    detail = client.get(f"/api/v1/incidents/{first.json()['incident_id']}").json()
    assert len(detail["alerts"]) == 2


def test_resolve_incident(client: TestClient) -> None:
    created = client.post("/api/v1/alerts", json=alert_payload()).json()
    response = client.post(f"/api/v1/incidents/{created['incident_id']}/resolve")

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
    assert response.json()["resolved_at"] is not None


def test_create_and_filter_deployment(client: TestClient) -> None:
    payload = {
        "service_name": "checkout-api",
        "environment": "production",
        "version": "2026.07.02.1",
        "commit_sha": "a1b2c3d4",
        "deployed_by": "fake-ci",
        "deployed_at": datetime.now(UTC).isoformat(),
        "metadata": {"pipeline": "deploy-123"},
    }
    created = client.post("/api/v1/deployments", json=payload)
    response = client.get("/api/v1/services/checkout-api/deployments")

    assert created.status_code == 201
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["metadata_json"] == {"pipeline": "deploy-123"}
