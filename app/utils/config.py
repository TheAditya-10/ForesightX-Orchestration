from shared import BaseServiceSettings


class OrchestrationSettings(BaseServiceSettings):
    service_name: str = "foresightx-orchestration"
    port: int = 8000
    data_service_url: str = "http://data:8001"
    profile_service_url: str = "http://profile:8002"
    pattern_service_url: str = "http://pattern:8003"
    request_timeout_seconds: float = 8.0
    max_retries: int = 2
    max_portfolio_exposure: float = 0.20
    high_volatility_threshold: float = 0.035
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
