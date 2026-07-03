import uuid

from app.db.session import SessionLocal
from app.services.pipeline import AnalysisPipeline
from app.worker import celery_app


@celery_app.task(
    bind=True,
    name="incidentpilot.analyze_incident",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def analyze_incident(self, incident_id: str) -> dict[str, str]:
    with SessionLocal() as db:
        analysis = AnalysisPipeline(db).run(uuid.UUID(incident_id))
        return {"incident_id": incident_id, "analysis_id": str(analysis.id)}
