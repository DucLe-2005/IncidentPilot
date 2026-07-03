from fastapi import APIRouter

from app.api.v1.routes import alerts, incidents, services

api_router = APIRouter()
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(services.router, tags=["service registry"])
