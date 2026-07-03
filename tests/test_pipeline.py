from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import EvidenceSource, Incident, Service
from app.services.pipeline import AnalysisPipeline, EvidenceResult


class FakePrometheusCollector:
    def collect(self, incident, service, source, window_start, window_end):
        return [
            EvidenceResult(
                type=source.type,
                source=source.name,
                summary=f"Elevated error rate for {service.name}",
                content={"query": source.config_json["query"], "value": 0.35},
            )
        ]


def test_placeholder_pipeline_creates_phase_one_artifacts(db_session: Session) -> None:
    incident = Incident(
        fingerprint="pipeline-test",
        alert_name="HighLatency",
        service_name="catalog-api",
        environment="production",
        severity="warning",
        status="open",
        started_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        last_seen_at=datetime(2026, 7, 2, 12, 5, tzinfo=UTC),
    )
    db_session.add(incident)
    db_session.commit()

    analysis = AnalysisPipeline(db_session).run(incident.id)
    db_session.refresh(incident)

    assert analysis.confidence == 0.0
    assert incident.status == "open"
    assert len(incident.analyses) == 1
    assert len(incident.notifications) == 1
    assert incident.notifications[0].channel == "console"
    assert incident.postmortem is not None


def test_reanalysis_does_not_reopen_resolved_incident(db_session: Session) -> None:
    incident = Incident(
        fingerprint="resolved-pipeline-test",
        alert_name="HighLatency",
        service_name="catalog-api",
        environment="production",
        severity="warning",
        status="resolved",
        started_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        last_seen_at=datetime(2026, 7, 2, 12, 5, tzinfo=UTC),
        resolved_at=datetime(2026, 7, 2, 12, 10, tzinfo=UTC),
    )
    db_session.add(incident)
    db_session.commit()

    AnalysisPipeline(db_session).run(incident.id)
    db_session.refresh(incident)

    assert incident.status == "resolved"


def test_pipeline_resolves_enabled_sources_from_service_registry(
    db_session: Session,
) -> None:
    service = Service(
        name="checkout-service",
        environment="prod",
        owner_team="commerce",
        slack_channel="#checkout-incidents",
        repo_url="https://github.com/example/checkout-service",
        runbook_url=None,
        tier=1,
    )
    db_session.add(service)
    db_session.flush()
    db_session.add_all(
        [
            EvidenceSource(
                service_id=service.id,
                type="metrics",
                provider="prometheus",
                name="production-prometheus",
                config_json={"query": "rate(errors_total[5m])"},
                enabled=True,
            ),
            EvidenceSource(
                service_id=service.id,
                type="logs",
                provider="loki",
                name="disabled-loki",
                config_json={},
                enabled=False,
            ),
        ]
    )
    incident = Incident(
        fingerprint="registry-pipeline-test",
        alert_name="HighErrorRate",
        service_name=service.name,
        environment=service.environment,
        severity="critical",
        status="open",
        started_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        last_seen_at=datetime(2026, 7, 3, 12, 5, tzinfo=UTC),
    )
    db_session.add(incident)
    db_session.commit()

    AnalysisPipeline(
        db_session,
        collectors={("metrics", "prometheus"): FakePrometheusCollector()},
    ).run(incident.id)
    db_session.refresh(incident)

    assert len(incident.evidence) == 1
    assert incident.evidence[0].source == "production-prometheus"
    assert incident.evidence[0].content_json["value"] == 0.35
