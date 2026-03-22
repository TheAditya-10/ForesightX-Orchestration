from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    request: dict[str, Any]
    validated_request: dict[str, Any]
    market_data: dict[str, Any]
    portfolio: dict[str, Any]
    analysis: dict[str, Any]
    decision: dict[str, Any]
    response: dict[str, Any]
    trace: dict[str, Any]
