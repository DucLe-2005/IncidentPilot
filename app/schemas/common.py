from pydantic import BaseModel


class AcceptedResponse(BaseModel):
    incident_id: str
    alert_id: str | None = None
    status: str = "accepted"


class HealthResponse(BaseModel):
    status: str
    service: str
