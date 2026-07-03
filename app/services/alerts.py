import hashlib
import json
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, Incident
from app.schemas.alerts import AlertCreate


def build_fingerprint(alert: AlertCreate) -> str:
    if alert.fingerprint:
        return alert.fingerprint
    identity = {
        "alert_name": alert.alert_name,
        "environment": alert.environment,
        "service_name": alert.service_name,
    }
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def ingest_alert(
    db: Session,
    payload: AlertCreate,
    enqueue: Callable[[str], None],
) -> tuple[Incident, Alert]:
    fingerprint = build_fingerprint(payload)
    incident = db.scalar(
        select(Incident)
        .where(Incident.fingerprint == fingerprint, Incident.status != "resolved")
        .with_for_update()
    )

    if incident is None:
        incident = Incident(
            fingerprint=fingerprint,
            alert_name=payload.alert_name,
            service_name=payload.service_name,
            environment=payload.environment,
            severity=payload.severity,
            status="resolved" if payload.status == "resolved" else "open",
            started_at=payload.started_at,
            last_seen_at=payload.ended_at or payload.started_at,
            resolved_at=payload.ended_at if payload.status == "resolved" else None,
        )
        db.add(incident)
        db.flush()
    else:
        incident.last_seen_at = payload.ended_at or payload.started_at
        incident.severity = payload.severity
        if payload.status == "resolved":
            incident.status = "resolved"
            incident.resolved_at = payload.ended_at or payload.started_at

    alert = Alert(
        incident_id=incident.id,
        alert_name=payload.alert_name,
        service_name=payload.service_name,
        environment=payload.environment,
        severity=payload.severity,
        status=payload.status,
        payload_json=payload.payload,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    db.refresh(incident)

    if payload.status == "firing":
        enqueue(str(incident.id))

    return incident, alert
