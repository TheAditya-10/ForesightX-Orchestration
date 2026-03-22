from copy import deepcopy

from shared import get_logger

from app.utils.config import OrchestrationSettings


class RiskManagementService:
    def __init__(self, settings: OrchestrationSettings) -> None:
        self.settings = settings
        self.logger = get_logger(settings.service_name, "risk")

    def apply(self, ticker: str, decision: dict, analysis: dict, portfolio: dict, price: dict) -> dict:
        adjusted = deepcopy(decision)
        reasons = list(adjusted["reason"])
        holdings = {item["ticker"]: item for item in portfolio["holdings"]}
        current_position_value = float(holdings.get(ticker, {}).get("current_value", 0.0))
        total_value = max(float(portfolio["total_value"]), 1.0)
        current_exposure = current_position_value / total_value

        if adjusted["action"] == "BUY":
            proposed_trade_value = min(float(portfolio["cash"]) * 0.10, total_value * 0.10)
            proposed_exposure = (current_position_value + proposed_trade_value) / total_value
            if proposed_exposure > self.settings.max_portfolio_exposure:
                adjusted["action"] = "HOLD"
                adjusted["confidence"] = min(float(adjusted["confidence"]), 0.62)
                reasons.append(
                    f"Risk check blocked BUY because projected exposure {proposed_exposure:.2%} exceeds the {self.settings.max_portfolio_exposure:.0%} cap."
                )

            if (
                analysis["volatility_proxy"] > self.settings.high_volatility_threshold
                and portfolio["risk_level"] != "high"
            ):
                adjusted["action"] = "HOLD"
                adjusted["confidence"] = min(float(adjusted["confidence"]), 0.58)
                reasons.append("Risk check blocked BUY because the volatility proxy is too high for the user's risk level.")

            if portfolio["risk_level"] == "low" and analysis["composite_score"] < 0.35:
                adjusted["action"] = "HOLD"
                adjusted["confidence"] = min(float(adjusted["confidence"]), 0.56)
                reasons.append("Low-risk account requires stronger conviction before opening new exposure.")

        if adjusted["action"] == "SELL" and current_position_value <= 0:
            adjusted["action"] = "HOLD"
            adjusted["confidence"] = min(float(adjusted["confidence"]), 0.55)
            reasons.append("Risk check blocked SELL because the portfolio has no current exposure in this ticker.")

        adjusted["confidence"] = round(float(adjusted["confidence"]), 2)
        adjusted["reason"] = reasons
        adjusted["risk_summary"] = {
            "current_exposure": round(current_exposure, 4),
            "volatility_proxy": analysis["volatility_proxy"],
            "risk_level": portfolio["risk_level"],
            "latest_price": price["price"],
        }
        self.logger.info(f"Risk-adjusted action for {ticker}: {adjusted['action']}")
        return adjusted
