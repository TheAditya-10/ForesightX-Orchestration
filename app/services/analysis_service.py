import math

from shared import get_logger


class SignalAnalysisService:
    def __init__(self, service_name: str) -> None:
        self.logger = get_logger(service_name, "signal-analysis")

    def combine_signals(self, ticker: str, market_data: dict, portfolio: dict) -> dict:
        price = float(market_data["price"]["price"])
        rsi = float(market_data["indicators"]["rsi"])
        macd = float(market_data["indicators"]["macd"])
        macd_signal = float(market_data["indicators"]["macd_signal"])
        sentiment_score = float(market_data["sentiment"]["sentiment_score"])
        sentiment_confidence = float(market_data["sentiment"]["confidence"])
        pattern_prediction = market_data["pattern"]["prediction"]
        pattern_confidence = float(market_data["pattern"]["confidence"])

        rsi_bias = (50 - rsi) / 50
        macd_bias = math.tanh(macd / max(price * 0.01, 0.01))
        crossover_bias = math.tanh((macd - macd_signal) / max(price * 0.005, 0.01))
        pattern_bias = {
            "bullish": 1.0,
            "neutral": 0.0,
            "bearish": -1.0,
        }.get(pattern_prediction, 0.0) * pattern_confidence
        sentiment_bias = sentiment_score * sentiment_confidence

        composite_score = (
            rsi_bias * 0.22
            + macd_bias * 0.23
            + crossover_bias * 0.15
            + pattern_bias * 0.25
            + sentiment_bias * 0.15
        )
        volatility_proxy = min(abs(macd) / max(price, 1.0) * 5, 1.0)

        reasons = [
            f"RSI is {rsi:.2f}, which maps to a momentum bias of {rsi_bias:.2f}.",
            f"MACD spread versus signal is {macd - macd_signal:.4f}, indicating trend strength of {crossover_bias:.2f}.",
            f"Pattern model predicts {pattern_prediction} with {pattern_confidence:.2f} confidence.",
            f"Headline sentiment scored {sentiment_score:.2f} with {sentiment_confidence:.2f} confidence.",
        ]
        self.logger.info(
            f"Combined signals for {ticker}: composite={composite_score:.3f}, volatility_proxy={volatility_proxy:.3f}"
        )
        return {
            "ticker": ticker,
            "price": price,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
            "pattern_prediction": pattern_prediction,
            "pattern_confidence": pattern_confidence,
            "sentiment_score": sentiment_score,
            "sentiment_confidence": sentiment_confidence,
            "portfolio_risk_level": portfolio["risk_level"],
            "composite_score": round(composite_score, 4),
            "volatility_proxy": round(volatility_proxy, 4),
            "analysis_reasons": reasons,
        }
