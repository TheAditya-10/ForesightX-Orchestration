from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.analyze import router as analyze_router
from app.schemas.analyze import AnalyzeResponse
from app.tools.service_tools import suggest_trade


class _RuntimeStub:
    async def search_instruments(self, query: str, limit: int = 15) -> dict:
        return {
            "query": query,
            "results": [
                {"ticker": "TCS.NS", "name": "Tata Consultancy Services", "exchange": "NSE", "score": 0.96},
                {"ticker": "TATAMOTORS.NS", "name": "Tata Motors", "exchange": "NSE", "score": 0.91},
            ][:limit],
        }


def test_suggest_trade_includes_recommendation() -> None:
    decision = suggest_trade(
        signals={"composite_score": 0.41, "pattern_prediction": "bullish", "pattern_confidence": 0.74},
        portfolio={"risk_level": "medium"},
    )
    assert decision["action"] == "BUY"
    assert isinstance(decision["recommendation"], str)
    assert len(decision["recommendation"]) > 10


def test_analyze_response_requires_recommendation() -> None:
    payload = AnalyzeResponse.model_validate(
        {
            "job_id": "job-1",
            "action": "HOLD",
            "confidence": 0.7,
            "reason": ["Mixed trend signals."],
            "recommendation": "Hold this position until trend confirmation improves.",
            "trace": {"tools_used": [], "execution_order": [], "intermediate_data": {}, "generated_at": "2026-04-19T10:00:00Z"},
        }
    )
    assert payload.recommendation.startswith("Hold")


def test_instrument_search_endpoint() -> None:
    app = FastAPI()
    app.include_router(analyze_router)
    app.state.runtime = _RuntimeStub()
    client = TestClient(app)

    response = client.get("/instruments/search", params={"q": "tata", "limit": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "tata"
    assert body["results"][0]["ticker"] == "TCS.NS"
