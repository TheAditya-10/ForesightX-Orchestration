import math

import httpx
from pydantic import BaseModel, Field

from shared import HTTPRequestError, request_json

from app.services.sentiment_service import score_headlines
from app.utils.config import OrchestrationSettings


class TickerInput(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)


class UserInput(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)


class TradeSuggestionInput(BaseModel):
    signals: dict
    portfolio: dict


async def get_stock_price(
    ticker: str,
    *,
    client: httpx.AsyncClient,
    settings: OrchestrationSettings,
    logger,
) -> dict:
    validated = TickerInput(ticker=ticker.strip().upper())
    return await request_json(
        client=client,
        method="GET",
        url=f"{settings.data_service_url.rstrip('/')}/price/{validated.ticker}",
        retries=settings.max_retries,
        logger=logger,
    )


async def get_indicators(
    ticker: str,
    *,
    client: httpx.AsyncClient,
    settings: OrchestrationSettings,
    logger,
) -> dict:
    validated = TickerInput(ticker=ticker.strip().upper())
    return await request_json(
        client=client,
        method="GET",
        url=f"{settings.data_service_url.rstrip('/')}/indicators/{validated.ticker}",
        retries=settings.max_retries,
        logger=logger,
    )


async def get_sentiment(
    ticker: str,
    *,
    client: httpx.AsyncClient,
    settings: OrchestrationSettings,
    logger,
) -> dict:
    validated = TickerInput(ticker=ticker.strip().upper())
    payload = await request_json(
        client=client,
        method="GET",
        url=f"{settings.data_service_url.rstrip('/')}/news/{validated.ticker}",
        retries=settings.max_retries,
        logger=logger,
    )
    sentiment = score_headlines(payload.get("headlines", []))
    return sentiment


async def get_user_portfolio(
    user_id: str,
    *,
    client: httpx.AsyncClient,
    settings: OrchestrationSettings,
    logger,
) -> dict:
    validated = UserInput(user_id=user_id.strip())
    return await request_json(
        client=client,
        method="GET",
        url=f"{settings.profile_service_url.rstrip('/')}/portfolio/{validated.user_id}",
        retries=settings.max_retries,
        logger=logger,
    )


async def predict_pattern(
    ticker: str,
    *,
    client: httpx.AsyncClient,
    settings: OrchestrationSettings,
    logger,
) -> dict:
    validated = TickerInput(ticker=ticker.strip().upper())
    try:
        return await request_json(
            client=client,
            method="POST",
            url=f"{settings.pattern_service_url.rstrip('/')}/predict",
            json={"ticker": validated.ticker},
            retries=settings.max_retries,
            logger=logger,
        )
    except HTTPRequestError as exc:
        error_message = str(exc).lower()
        if "404" in error_message:
            logger.warning(
                "Pattern prediction unavailable for ticker; using neutral fallback",
                extra={"ticker": validated.ticker},
            )
            return {
                "symbol": validated.ticker,
                "prediction": "neutral",
                "confidence": 0.5,
                "predicted_return": 0.0,
                "latest_close": 0.0,
                "predicted_next_close": 0.0,
            }
        raise


def suggest_trade(signals: dict, portfolio: dict) -> dict:
    validated = TradeSuggestionInput(signals=signals, portfolio=portfolio)
    composite = float(validated.signals["composite_score"])
    pattern_prediction = validated.signals["pattern_prediction"]
    pattern_confidence = float(validated.signals["pattern_confidence"])
    risk_level = validated.portfolio["risk_level"]

    action = "HOLD"
    if composite >= 0.28 and pattern_prediction == "bullish":
        action = "BUY"
    elif composite <= -0.28 and pattern_prediction == "bearish":
        action = "SELL"

    if risk_level == "low" and action == "BUY" and composite < 0.4:
        action = "HOLD"

    confidence = min(0.52 + abs(composite) * 0.5 + pattern_confidence * 0.2, 0.93)
    rationale = [
        f"Composite signal score is {composite:.2f}.",
        f"Pattern model points {pattern_prediction} with {pattern_confidence:.2f} confidence.",
        f"Portfolio risk level is {risk_level}.",
    ]
    if math.isclose(composite, 0.0, abs_tol=0.05):
        rationale.append("Signals are too balanced to justify a directional trade.")

    return {
        "action": action,
        "confidence": round(confidence, 2),
        "reason": rationale,
    }
