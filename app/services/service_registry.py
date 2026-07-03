import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import EvidenceSource, Service
from app.schemas.services import EvidenceSourceCreate, ServiceCreate


def create_service(db: Session, payload: ServiceCreate) -> Service:
    service = Service(
        name=payload.name,
        environment=payload.environment,
        owner_team=payload.owner_team,
        slack_channel=payload.slack_channel,
        repo_url=str(payload.repo_url) if payload.repo_url else None,
        runbook_url=str(payload.runbook_url) if payload.runbook_url else None,
        tier=payload.tier,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def list_services(
    db: Session,
    *,
    environment: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Service]:
    statement = select(Service).order_by(Service.name).limit(limit).offset(offset)
    if environment:
        statement = statement.where(Service.environment == environment)
    return list(db.scalars(statement))


def get_service(db: Session, service_id: uuid.UUID) -> Service | None:
    return db.scalar(
        select(Service)
        .where(Service.id == service_id)
        .options(selectinload(Service.evidence_sources))
    )


def find_service(db: Session, name: str, environment: str) -> Service | None:
    return db.scalar(
        select(Service).where(Service.name == name, Service.environment == environment)
    )


def create_evidence_source(
    db: Session, service: Service, payload: EvidenceSourceCreate
) -> EvidenceSource:
    source = EvidenceSource(
        service_id=service.id,
        type=payload.type,
        provider=payload.provider,
        name=payload.name,
        config_json=payload.config,
        enabled=payload.enabled,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def list_enabled_evidence_sources(db: Session, service_id: uuid.UUID) -> list[EvidenceSource]:
    return list(
        db.scalars(
            select(EvidenceSource)
            .where(
                EvidenceSource.service_id == service_id,
                EvidenceSource.enabled.is_(True),
            )
            .order_by(EvidenceSource.type, EvidenceSource.name)
        )
    )


def get_evidence_source(db: Session, source_id: uuid.UUID) -> EvidenceSource | None:
    return db.get(EvidenceSource, source_id)


def set_evidence_source_enabled(
    db: Session, source: EvidenceSource, *, enabled: bool
) -> EvidenceSource:
    source.enabled = enabled
    db.commit()
    db.refresh(source)
    return source
