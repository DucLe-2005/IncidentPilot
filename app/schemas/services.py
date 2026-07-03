import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

EvidenceType = Literal["metrics", "logs", "deployments", "code"]


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    environment: str = Field(min_length=1, max_length=100)
    owner_team: str = Field(min_length=1, max_length=255)
    slack_channel: str | None = Field(default=None, max_length=255)
    repo_url: HttpUrl | None = None
    runbook_url: HttpUrl | None = None
    tier: int = Field(ge=1, le=4)


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    environment: str
    owner_team: str
    slack_channel: str | None
    repo_url: str | None
    runbook_url: str | None
    tier: int
    created_at: datetime
    updated_at: datetime


class EvidenceSourceCreate(BaseModel):
    type: EvidenceType
    provider: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class EvidenceSourceUpdate(BaseModel):
    enabled: bool


class EvidenceSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    type: str
    provider: str
    name: str
    config_json: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ServiceDetail(ServiceRead):
    evidence_sources: list[EvidenceSourceRead]
