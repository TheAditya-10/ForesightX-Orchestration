from pathlib import Path

from pydantic import field_validator
from pydantic_settings import SettingsConfigDict

from shared import BaseServiceSettings, normalize_postgres_async_url


class OrchestrationSettings(BaseServiceSettings):
    service_name: str = "foresightx-orchestration"
    port: int = 8000
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/foresightx_orchestration"
    data_service_url: str = "http://data:8001"
    profile_service_url: str = "http://profile:8002"
    pattern_service_url: str = "http://pattern:8003"
    request_timeout_seconds: float = 8.0
    max_retries: int = 2
    max_portfolio_exposure: float = 0.20
    high_volatility_threshold: float = 0.035
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return normalize_postgres_async_url(value)
