# ForesightX Orchestration Service

This is the decision engine of the platform.

## Responsibilities

- receive market-event analysis requests
- execute tools against other services
- combine and normalize signals
- use Gemini for structured decisions
- apply deterministic risk checks
- return explainable responses with trace data

## API

- `POST /analyze`
- `GET /health`

## Workflow

- `event_node`
- `data_fetch_node`
- `analysis_node`
- `decision_node`
- `risk_check_node`
- `response_node`
