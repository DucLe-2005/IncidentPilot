import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import DbSession
from app.schemas.services import (
    EvidenceSourceCreate,
    EvidenceSourceRead,
    EvidenceSourceUpdate,
    ServiceCreate,
    ServiceDetail,
    ServiceRead,
)
from app.services import service_registry

router = APIRouter()


def _service_or_404(db: DbSession, service_id: uuid.UUID):
    service = service_registry.get_service(db, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.post("/services", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, db: DbSession) -> ServiceRead:
    try:
        return service_registry.create_service(db, payload)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A service with this name and environment already exists",
        ) from error


@router.get("/services", response_model=list[ServiceRead])
def list_services(
    db: DbSession,
    environment: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ServiceRead]:
    return service_registry.list_services(db, environment=environment, limit=limit, offset=offset)


@router.get("/services/{service_id}", response_model=ServiceDetail)
def get_service(service_id: uuid.UUID, db: DbSession) -> ServiceDetail:
    return _service_or_404(db, service_id)


@router.post(
    "/services/{service_id}/evidence-sources",
    response_model=EvidenceSourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence_source(
    service_id: uuid.UUID, payload: EvidenceSourceCreate, db: DbSession
) -> EvidenceSourceRead:
    service = _service_or_404(db, service_id)
    try:
        return service_registry.create_evidence_source(db, service, payload)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An evidence source with this name already exists for the service",
        ) from error


@router.patch("/evidence-sources/{source_id}", response_model=EvidenceSourceRead)
def update_evidence_source(
    source_id: uuid.UUID, payload: EvidenceSourceUpdate, db: DbSession
) -> EvidenceSourceRead:
    source = service_registry.get_evidence_source(db, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence source not found"
        )
    return service_registry.set_evidence_source_enabled(db, source, enabled=payload.enabled)
