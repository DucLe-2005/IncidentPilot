from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Deployment
from app.schemas.deployments import DeploymentCreate


def create_deployment(db: Session, payload: DeploymentCreate) -> Deployment:
    deployment = Deployment(
        service_name=payload.service_name,
        environment=payload.environment,
        version=payload.version,
        commit_sha=payload.commit_sha,
        deployed_by=payload.deployed_by,
        deployed_at=payload.deployed_at,
        metadata_json=payload.metadata,
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment


def list_deployments(
    db: Session,
    *,
    service_name: str | None = None,
    environment: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Deployment]:
    statement = (
        select(Deployment).order_by(Deployment.deployed_at.desc()).limit(limit).offset(offset)
    )
    if service_name:
        statement = statement.where(Deployment.service_name == service_name)
    if environment:
        statement = statement.where(Deployment.environment == environment)
    return list(db.scalars(statement))
