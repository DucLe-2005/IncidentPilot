import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeploymentCreate(BaseModel):
    service_name: str = Field(min_length=1, max_length=255)
    environment: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=255)
    commit_sha: str = Field(min_length=7, max_length=64)
    deployed_by: str = Field(min_length=1, max_length=255)
    deployed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeploymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_name: str
    environment: str
    version: str
    commit_sha: str
    deployed_by: str
    deployed_at: datetime
    metadata_json: dict[str, Any]
    created_at: datetime
