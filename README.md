# IncidentPilot

IncidentPilot is the phase-one foundation for an autonomous incident response system. It
accepts alerts, deduplicates them into incidents, queues background analysis, stores evidence
and analysis artifacts, records deployments, emits notifications, and drafts postmortems.

Provider-specific alert ingestion, telemetry collection, LLM calls, Slack/email delivery, and
postmortem policy are intentionally isolated behind the pipeline boundary for later phases.

## Architecture

```text
Alert source -> FastAPI -> PostgreSQL
                    |
                    +-> Redis -> Celery worker
                                   |
                                   +-> evidence collectors (future adapters)
                                   +-> incident analyzer (future LLM adapter)
                                   +-> notification adapters (future Slack/email)
                                   +-> postmortem draft
```

The repository is organized by responsibility:

```text
app/
  api/v1/routes/    HTTP contracts
  core/             configuration and logging
  db/               SQLAlchemy session and metadata
  models/           persistent entities
  schemas/          Pydantic request/response models
  services/         application use cases and pipeline orchestration
  tasks/            Celery task entry points
migrations/         Alembic database migrations
tests/              API behavior tests
```

## Run locally

Prerequisites: Docker with Compose v2.

```bash
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`, with OpenAPI documentation at
`http://localhost:8000/docs`. PostgreSQL and Redis are exposed on their standard local ports
for development.

Send a sample alert:

```bash
curl -X POST http://localhost:8000/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "HighErrorRate",
    "service_name": "checkout-api",
    "environment": "production",
    "severity": "critical",
    "status": "firing",
    "payload": {"error_rate": 0.35}
  }'
```

## API surface

- `POST /api/v1/alerts`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{incident_id}`
- `POST /api/v1/incidents/{incident_id}/resolve`
- `POST /api/v1/incidents/{incident_id}/reanalyze`
- `POST /api/v1/deployments`
- `GET /api/v1/deployments`
- `GET /api/v1/services/{service_name}/deployments`
- `GET /health`
- `GET /ready`

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Current worker behavior

The worker has a runnable placeholder analyzer so the end-to-end lifecycle can be exercised
without external credentials. It stores an analysis with zero confidence, writes a console
notification, and creates or updates a postmortem draft. Add evidence collectors and replace
`PlaceholderAnalyzer` in `app/services/pipeline.py` when provider decisions are made.
