import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Incident

DETAIL_LOADS = (
    selectinload(Incident.alerts),
    selectinload(Incident.evidence),
    selectinload(Incident.analyses),
    selectinload(Incident.notifications),
    selectinload(Incident.postmortem),
)


def list_incidents(
    db: Session,
    *,
    status: str | None = None,
    service_name: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Incident]:
    statement = select(Incident).order_by(Incident.created_at.desc()).limit(limit).offset(offset)
    if status:
        statement = statement.where(Incident.status == status)
    if service_name:
        statement = statement.where(Incident.service_name == service_name)
    return list(db.scalars(statement))


def get_incident(db: Session, incident_id: uuid.UUID) -> Incident | None:
    return db.scalar(select(Incident).where(Incident.id == incident_id).options(*DETAIL_LOADS))


def resolve_incident(db: Session, incident: Incident) -> Incident:
    if incident.status != "resolved":
        incident.status = "resolved"
        incident.resolved_at = datetime.now(UTC)
        db.commit()
        db.refresh(incident)
    return incident


def reanalyze_incident(db: Session, incident: Incident, enqueue: Callable[[str], None]) -> Incident:
    enqueue(str(incident.id))
    return incident
