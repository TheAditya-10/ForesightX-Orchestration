# ForesightX Orchestration Service

This is the decision engine of the platform.

## Responsibilities

- receive market-event analysis requests
- execute tools against other services
- combine and normalize signals
- use Gemini for structured decisions
- apply deterministic risk checks
- return explainable responses with trace data
- persist analysis jobs and ordered workflow events in its own database

## API

- `POST /analyze`
- `GET /analysis/jobs`
- `GET /analysis/jobs/{job_id}`
- `GET /health`

## Workflow

- `event_node`
- `data_fetch_node`
- `analysis_node`
- `decision_node`
- `risk_check_node`
- `response_node`

## Configuration

This service is independently configured from `ForesightX-orchestration/.env`.

Key variables:

- `DATABASE_URL`
- `DATA_SERVICE_URL`
- `PROFILE_SERVICE_URL`
- `PATTERN_SERVICE_URL`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`

Schema ownership:

- `analysis_jobs`: one row per orchestration request with final status and decision summary
- `analysis_job_events`: ordered node-level trace payloads for explainability and auditability

Before first startup:

```bash
alembic upgrade head
```
