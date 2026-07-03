import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Analysis, Evidence, Incident, Notification, Postmortem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceResult:
    type: str
    source: str
    summary: str
    content: dict[str, Any]


@dataclass(frozen=True)
class AnalysisResult:
    summary: str
    likely_root_cause: str
    impact_summary: str
    recommended_actions: list[dict[str, Any]]
    confidence: float
    raw_output: dict[str, Any]


class EvidenceCollector(Protocol):
    def collect(
        self, incident: Incident, window_start: datetime, window_end: datetime
    ) -> list[EvidenceResult]: ...


class IncidentAnalyzer(Protocol):
    def analyze(self, incident: Incident, evidence: list[Evidence]) -> AnalysisResult: ...


class PlaceholderAnalyzer:
    """Replace with a provider-backed analyzer in a later phase."""

    def analyze(self, incident: Incident, evidence: list[Evidence]) -> AnalysisResult:
        return AnalysisResult(
            summary=f"Analysis requested for {incident.alert_name} on {incident.service_name}.",
            likely_root_cause="Not determined: no LLM provider is configured.",
            impact_summary=f"Severity reported as {incident.severity}; impact requires validation.",
            recommended_actions=[
                {"action": "Inspect service telemetry", "owner": "on-call", "status": "open"}
            ],
            confidence=0.0,
            raw_output={"provider": "placeholder", "evidence_count": len(evidence)},
        )


class AnalysisPipeline:
    def __init__(
        self,
        db: Session,
        collectors: list[EvidenceCollector] | None = None,
        analyzer: IncidentAnalyzer | None = None,
    ) -> None:
        self.db = db
        self.collectors = collectors or []
        self.analyzer = analyzer or PlaceholderAnalyzer()

    def run(self, incident_id: uuid.UUID) -> Analysis:
        incident = self.db.scalar(
            select(Incident).where(Incident.id == incident_id).with_for_update()
        )
        if incident is None:
            raise ValueError(f"Incident {incident_id} does not exist")

        previous_status = incident.status
        incident.status = "analyzing"
        self.db.commit()

        try:
            evidence = self._collect_evidence(incident)
            result = self.analyzer.analyze(incident, evidence)
            analysis = self._store_analysis(incident, result)
            self._create_console_notification(incident, analysis)
            self._upsert_postmortem(incident, analysis)
            incident.status = "resolved" if previous_status == "resolved" else "open"
            self.db.commit()
            self.db.refresh(analysis)
            return analysis
        except Exception:
            self.db.rollback()
            incident = self.db.get(Incident, incident_id)
            if incident is not None:
                incident.status = "analysis_failed"
                self.db.commit()
            raise

    def _collect_evidence(self, incident: Incident) -> list[Evidence]:
        window_end = incident.last_seen_at
        window_start = window_end - timedelta(minutes=settings.evidence_window_minutes)
        records: list[Evidence] = []
        for collector in self.collectors:
            for result in collector.collect(incident, window_start, window_end):
                record = Evidence(
                    incident_id=incident.id,
                    type=result.type,
                    source=result.source,
                    time_window_start=window_start,
                    time_window_end=window_end,
                    summary=result.summary,
                    content_json=result.content,
                )
                self.db.add(record)
                records.append(record)
        self.db.flush()
        return records

    def _store_analysis(self, incident: Incident, result: AnalysisResult) -> Analysis:
        analysis = Analysis(
            incident_id=incident.id,
            summary=result.summary,
            likely_root_cause=result.likely_root_cause,
            impact_summary=result.impact_summary,
            recommended_actions_json=result.recommended_actions,
            confidence=result.confidence,
            analysis_version="v1",
            model_name=settings.llm_model,
            raw_output_json=result.raw_output,
        )
        self.db.add(analysis)
        self.db.flush()
        return analysis

    def _create_console_notification(self, incident: Incident, analysis: Analysis) -> None:
        message = (
            f"[{incident.severity.upper()}] {incident.service_name}: {analysis.summary} "
            f"Likely cause: {analysis.likely_root_cause}"
        )
        logger.info("incident_notification incident_id=%s message=%s", incident.id, message)
        self.db.add(
            Notification(
                incident_id=incident.id,
                channel="console",
                destination="stdout",
                status="sent",
                message=message,
                provider_message_id=None,
                sent_at=datetime.now(UTC),
            )
        )

    def _upsert_postmortem(self, incident: Incident, analysis: Analysis) -> None:
        postmortem = self.db.scalar(select(Postmortem).where(Postmortem.incident_id == incident.id))
        timeline = [
            {"timestamp": incident.started_at.isoformat(), "event": "Incident started"},
            {"timestamp": incident.last_seen_at.isoformat(), "event": "Latest alert observed"},
        ]
        markdown = (
            f"# {incident.alert_name} on {incident.service_name}\n\n"
            f"## Summary\n{analysis.summary}\n\n"
            f"## Impact\n{analysis.impact_summary}\n\n"
            f"## Root cause\n{analysis.likely_root_cause}\n"
        )
        values = {
            "title": f"{incident.alert_name} on {incident.service_name}",
            "summary": analysis.summary,
            "impact": analysis.impact_summary,
            "root_cause": analysis.likely_root_cause,
            "timeline_json": timeline,
            "action_items_json": analysis.recommended_actions_json,
            "markdown_content": markdown,
        }
        if postmortem is None:
            self.db.add(Postmortem(incident_id=incident.id, **values))
        else:
            for key, value in values.items():
                setattr(postmortem, key, value)
