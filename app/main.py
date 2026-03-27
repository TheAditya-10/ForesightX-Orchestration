from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import lru_cache

from fastapi import FastAPI

from shared import ServiceHealth, build_async_client, configure_logging, get_logger

from app.db.session import check_database_connection, close_database, get_session_factory
from app.routers.analyze import router as analyze_router
from app.services.runtime import OrchestrationRuntime
from app.utils.config import OrchestrationSettings


@lru_cache(maxsize=1)
def get_settings() -> OrchestrationSettings:
    return OrchestrationSettings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.service_name, settings.log_level)
    logger = get_logger(settings.service_name, "startup")
    session_factory = get_session_factory(settings.database_url)
    await check_database_connection(settings.database_url)
    runtime = OrchestrationRuntime(
        settings=settings,
        http_client=build_async_client(timeout=settings.request_timeout_seconds),
        session_factory=session_factory,
    )
    await runtime.start()
    app.state.runtime = runtime
    app.state.settings = settings
    app.state.session_factory = session_factory
    logger.info("Orchestration service startup complete")
    try:
        yield
    finally:
        await runtime.close()
        await close_database()
        logger.info("Orchestration service shutdown complete")


app = FastAPI(title="ForesightX Orchestration Service", version="0.1.0", lifespan=lifespan)
app.include_router(analyze_router)


@app.get("/health", response_model=ServiceHealth)
async def healthcheck() -> ServiceHealth:
    settings = get_settings()
    return ServiceHealth(
        service=settings.service_name,
        status="ok",
        timestamp=datetime.now(timezone.utc),
    )
