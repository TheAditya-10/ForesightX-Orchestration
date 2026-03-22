# Orchestration Tools

Tools are the orchestration layer's callable integration units.

Each tool:

- validates input
- calls another microservice over HTTP when required
- returns a structured dictionary

This directory is the MCP-style boundary between decision logic and external capabilities.
