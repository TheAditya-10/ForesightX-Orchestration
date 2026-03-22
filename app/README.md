# Orchestration App Package

This package contains the runtime code for controlled execution.

The package is split so each concern has a clear home:

- routers for HTTP entry points
- graph for workflow definition
- tools for inter-service calls
- services for analysis, LLM decisioning, and risk logic
- schemas for public contracts
