from __future__ import annotations

import asyncio

import pytest

from app.tools import service_tools
from app.utils.config import OrchestrationSettings


def test_search_instruments_returns_empty_for_blank_query() -> None:
    async def _run() -> None:
        settings = OrchestrationSettings(data_service_url="http://data")
        results = await service_tools.search_instruments("  ", client=None, settings=settings, logger=None)  # type: ignore[arg-type]
        assert results == {"query": "", "results": []}

    asyncio.run(_run())


def test_predict_pattern_falls_back_on_404(monkeypatch) -> None:
    async def _run() -> None:
        settings = OrchestrationSettings(pattern_service_url="http://pattern")

        class _Logger:
            def warning(self, *_args, **_kwargs):
                return None

        async def _raise_404(**_kwargs):
            raise service_tools.HTTPRequestError("404 not found")

        monkeypatch.setattr(service_tools, "request_json", _raise_404)
        payload = await service_tools.predict_pattern("tcs.ns", client=None, settings=settings, logger=_Logger())  # type: ignore[arg-type]
        assert payload["prediction"] == "neutral"
        assert payload["symbol"] == "TCS.NS"

    asyncio.run(_run())


def test_get_stock_price_uppercases_ticker_and_builds_url(monkeypatch) -> None:
    async def _run() -> None:
        settings = OrchestrationSettings(data_service_url="http://data")
        captured = {}

        async def _fake_request_json(**kwargs):  # noqa: ANN003
            captured.update(kwargs)
            return {"ok": True}

        monkeypatch.setattr(service_tools, "request_json", _fake_request_json)
        await service_tools.get_stock_price(" tcs.ns ", client=None, settings=settings, logger=None)  # type: ignore[arg-type]
        assert captured["url"].endswith("/price/TCS.NS")

    asyncio.run(_run())


def test_suggest_trade_handles_low_risk_buy_downgrade() -> None:
    decision = service_tools.suggest_trade(
        signals={"composite_score": 0.3, "pattern_prediction": "bullish", "pattern_confidence": 0.2},
        portfolio={"risk_level": "low"},
    )
    assert decision["action"] == "HOLD"
    assert isinstance(decision["recommendation"], str)


def test_suggest_trade_rejects_invalid_payload() -> None:
    with pytest.raises(Exception):
        service_tools.suggest_trade(signals={}, portfolio={})
