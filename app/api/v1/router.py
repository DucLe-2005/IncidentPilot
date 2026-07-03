from fastapi import APIRouter

from app.api.v1.routes import alerts, deployments, incidents

api_router = APIRouter()
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(deployments.router, tags=["deployments"])
