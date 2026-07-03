from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Incident
from app.services.pipeline import AnalysisPipeline


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
