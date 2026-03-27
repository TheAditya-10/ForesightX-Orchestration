from typing import Any, Literal
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    ticker: str = Field(..., min_length=1, max_length=20)
    event: Literal["market_update", "portfolio_rebalance", "risk_alert"] = "market_update"

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()


class DecisionPayload(BaseModel):
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(..., ge=0, le=1)
    reason: list[str] = Field(..., min_length=1)


class TracePayload(BaseModel):
    tools_used: list[str]
    execution_order: list[str]
    intermediate_data: dict[str, Any]
    generated_at: str | None = None


class AnalyzeResponse(BaseModel):
    job_id: str | None = None
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(..., ge=0, le=1)
    reason: list[str]
    trace: TracePayload


class AnalysisJobEventResponse(BaseModel):
    sequence_number: int
    node_name: str
    tools_used: list[str]
    payload: dict[str, Any] | None = None
    created_at: datetime


class AnalysisJobResponse(BaseModel):
    job_id: str
    user_id: str
    ticker: str
    event: str
    status: str
    action: str | None = None
    confidence: float | None = None
    reasons: list[str] = Field(default_factory=list)
    failure_reason: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    events: list[AnalysisJobEventResponse] = Field(default_factory=list)


class AnalysisJobListResponse(BaseModel):
    jobs: list[AnalysisJobResponse]
