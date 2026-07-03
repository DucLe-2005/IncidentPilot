# IncidentPilot

IncidentPilot is the phase-one foundation for an autonomous incident response system. It
accepts alerts, deduplicates them into incidents, queues background analysis, stores evidence
and analysis artifacts, emits notifications, and drafts postmortems.

Provider-specific alert ingestion, telemetry collection, LLM calls, Slack/email delivery, and
postmortem policy are intentionally isolated behind the pipeline boundary for later phases.

## Architecture

```text
Alert source -> FastAPI -> PostgreSQL
                    |
                    +-> Redis -> Celery worker
                                   |
                                   +-> service registry
                                   +-> enabled evidence source definitions
                                   +-> provider collectors (future adapters)
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

For live backend and worker reloading during development:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

`compose.dev.yaml` bind-mounts the application package. Uvicorn reloads when backend Python
files change, while `watchfiles` restarts the Celery worker process when worker or shared
application code changes. The base `compose.yaml` runs stable processes without bind mounts.

Database tables are created directly from the SQLAlchemy models by the `init-db` Compose
service. During this development phase, make schema changes in `app/models/entities.py`. Since
`create_all()` does not alter existing columns, recreate the local database after incompatible
schema changes:

```bash
docker compose -f compose.yaml -f compose.dev.yaml down --volumes
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

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
- `POST /api/v1/services`
- `GET /api/v1/services`
- `GET /api/v1/services/{service_id}`
- `POST /api/v1/services/{service_id}/evidence-sources`
- `PATCH /api/v1/evidence-sources/{source_id}`
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

Run the test suite in Docker:

```bash
docker compose -f compose.test.yml run --rm test
```

The test image installs development dependencies and runs the bind-mounted test suite from
`/tests`, so local application and test changes are used without rebuilding the image.

## Current worker behavior

The worker has a runnable placeholder analyzer so the end-to-end lifecycle can be exercised
without external credentials. It stores an analysis with zero confidence, writes a console
notification, and creates or updates a postmortem draft. Add evidence collectors and replace
`PlaceholderAnalyzer` in `app/services/pipeline.py` when provider decisions are made.

## Service and evidence-source registry

An alert identifies a service by `service_name` and `environment`. The worker resolves that
pair against the `services` table, loads enabled rows from `evidence_sources`, and dispatches
each source to a collector registered for its `(type, provider)` pair. Collected output is
written to `evidence` and remains tied to the incident.

Deployments are not stored as a separate domain table. Configure deployment systems as
`evidence_sources` with type `deployments`; collected deployment events are stored in the
incident-scoped `evidence` table.

`evidence_sources.config_json` should contain query configuration and secret references, not
raw credentials. Provider adapters can resolve referenced credentials from the runtime secret
store when they are added.
