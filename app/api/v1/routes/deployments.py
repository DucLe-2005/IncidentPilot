from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import DbSession
from app.schemas.deployments import DeploymentCreate, DeploymentRead
from app.services import deployments as deployment_service

router = APIRouter()


@router.post("/deployments", response_model=DeploymentRead, status_code=status.HTTP_201_CREATED)
def create_deployment(payload: DeploymentCreate, db: DbSession) -> DeploymentRead:
    return deployment_service.create_deployment(db, payload)


@router.get("/deployments", response_model=list[DeploymentRead])
def list_deployments(
    db: DbSession,
    service_name: str | None = None,
    environment: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DeploymentRead]:
    return deployment_service.list_deployments(
        db,
        service_name=service_name,
        environment=environment,
        limit=limit,
        offset=offset,
    )


@router.get("/services/{service_name}/deployments", response_model=list[DeploymentRead])
def list_service_deployments(
    service_name: str,
    db: DbSession,
    environment: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DeploymentRead]:
    return deployment_service.list_deployments(
        db,
        service_name=service_name,
        environment=environment,
        limit=limit,
        offset=offset,
    )
