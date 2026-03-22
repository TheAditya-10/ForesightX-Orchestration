from typing import Any, Literal

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
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(..., ge=0, le=1)
    reason: list[str]
    trace: TracePayload
