from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    alert_name: str = Field(min_length=1, max_length=255)
    service_name: str = Field(min_length=1, max_length=255)
    environment: str = Field(min_length=1, max_length=100)
    severity: Literal["info", "warning", "critical"]
    status: Literal["firing", "resolved"] = "firing"
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    fingerprint: str | None = Field(default=None, max_length=64)
