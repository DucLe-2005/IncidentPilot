from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "incidentpilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.incidents"],
)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
