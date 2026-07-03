import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DbSession
from app.schemas.common import AcceptedResponse
from app.schemas.incidents import IncidentDetail, IncidentRead
from app.services import incidents as incident_service

router = APIRouter()


def enqueue_analysis(incident_id: str) -> None:
    from app.tasks.incidents import analyze_incident

    analyze_incident.delay(incident_id)


def _get_or_404(db: DbSession, incident_id: uuid.UUID):
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("", response_model=list[IncidentRead])
def list_incidents(
    db: DbSession,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    service_name: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[IncidentRead]:
    return incident_service.list_incidents(
        db,
        status=status_filter,
        service_name=service_name,
        limit=limit,
        offset=offset,
    )


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: uuid.UUID, db: DbSession) -> IncidentDetail:
    return _get_or_404(db, incident_id)


@router.post("/{incident_id}/resolve", response_model=IncidentRead)
def resolve_incident(incident_id: uuid.UUID, db: DbSession) -> IncidentRead:
    return incident_service.resolve_incident(db, _get_or_404(db, incident_id))


@router.post(
    "/{incident_id}/reanalyze",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def reanalyze_incident(incident_id: uuid.UUID, db: DbSession) -> AcceptedResponse:
    incident = incident_service.reanalyze_incident(
        db, _get_or_404(db, incident_id), enqueue_analysis
    )
    return AcceptedResponse(incident_id=str(incident.id))
