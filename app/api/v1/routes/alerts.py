from fastapi import APIRouter, status

from app.api.dependencies import DbSession
from app.schemas.alerts import AlertCreate
from app.schemas.common import AcceptedResponse
from app.services.alerts import ingest_alert

router = APIRouter()


def enqueue_analysis(incident_id: str) -> None:
    from app.tasks.incidents import analyze_incident

    analyze_incident.delay(incident_id)


@router.post("", response_model=AcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def receive_alert(payload: AlertCreate, db: DbSession) -> AcceptedResponse:
    incident, alert = ingest_alert(db, payload, enqueue_analysis)
    return AcceptedResponse(incident_id=str(incident.id), alert_id=str(alert.id))
