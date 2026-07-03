import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    alert_name: str
    service_name: str
    environment: str
    severity: str
    status: str
    payload_json: dict[str, Any]
    received_at: datetime
    started_at: datetime
    ended_at: datetime | None


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    source: str
    time_window_start: datetime
    time_window_end: datetime
    summary: str
    content_json: dict[str, Any]
    created_at: datetime


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    summary: str
    likely_root_cause: str
    impact_summary: str
    recommended_actions_json: list[dict[str, Any]]
    confidence: float
    analysis_version: str
    model_name: str
    raw_output_json: dict[str, Any]
    created_at: datetime


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: str
    destination: str
    status: str
    message: str
    provider_message_id: str | None
    error_message: str | None
    created_at: datetime
    sent_at: datetime | None


class PostmortemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    summary: str
    impact: str
    root_cause: str
    timeline_json: list[dict[str, Any]]
    action_items_json: list[dict[str, Any]]
    markdown_content: str
    created_at: datetime
    updated_at: datetime


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fingerprint: str
    alert_name: str
    service_name: str
    environment: str
    severity: str
    status: str
    created_at: datetime
    started_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None
    updated_at: datetime


class IncidentDetail(IncidentRead):
    alerts: list[AlertRead]
    evidence: list[EvidenceRead]
    analyses: list[AnalysisRead]
    notifications: list[NotificationRead]
    postmortem: PostmortemRead | None
