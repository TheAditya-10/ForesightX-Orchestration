# Orchestration Services

This directory contains the internal logic used by the workflow.

## Modules

- `analysis_service.py`: signal normalization and composite scoring
- `decision_service.py`: Gemini prompt construction and strict JSON parsing
- `risk_service.py`: exposure and volatility guardrails
- `runtime.py`: service bootstrap and graph invocation
- `sentiment_service.py`: headline scoring from news payloads
