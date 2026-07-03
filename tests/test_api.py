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


def test_configure_service_and_evidence_source(client: TestClient) -> None:
    service_response = client.post(
        "/api/v1/services",
        json={
            "name": "checkout-service",
            "environment": "prod",
            "owner_team": "commerce",
            "slack_channel": "#checkout-incidents",
            "repo_url": "https://github.com/example/checkout-service",
            "runbook_url": "https://runbooks.example.com/checkout-service",
            "tier": 1,
        },
    )
    assert service_response.status_code == 201
    service_id = service_response.json()["id"]

    source_response = client.post(
        f"/api/v1/services/{service_id}/evidence-sources",
        json={
            "type": "metrics",
            "provider": "prometheus",
            "name": "production-prometheus",
            "config": {
                "base_url": "http://prometheus:9090",
                "query_template": 'rate(http_requests_total{service="$service"}[5m])',
            },
            "enabled": True,
        },
    )
    assert source_response.status_code == 201

    detail = client.get(f"/api/v1/services/{service_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "checkout-service"
    assert detail.json()["evidence_sources"][0]["provider"] == "prometheus"

    source_id = source_response.json()["id"]
    disabled = client.patch(f"/api/v1/evidence-sources/{source_id}", json={"enabled": False})
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False


def test_rejects_duplicate_service_registration(client: TestClient) -> None:
    payload = {
        "name": "payment-service",
        "environment": "prod",
        "owner_team": "payments",
        "tier": 1,
    }
    assert client.post("/api/v1/services", json=payload).status_code == 201
    assert client.post("/api/v1/services", json=payload).status_code == 409
