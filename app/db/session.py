from collections.abc import AsyncIterator

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.db.models import AnalysisJob


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(database_url: str) -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def get_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(database_url), expire_on_commit=False)
    return _session_factory


async def get_db_session(database_url: str) -> AsyncIterator[AsyncSession]:
    async with get_session_factory(database_url)() as session:
        yield session


async def check_database_connection(database_url: str) -> None:
    async with get_engine(database_url).connect() as connection:
        await connection.execute(text("SELECT 1"))


async def close_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def get_job_with_events(session: AsyncSession, job_id: str) -> AnalysisJob | None:
    try:
        normalized_job_id = uuid.UUID(job_id)
    except ValueError:
        return None
    result = await session.execute(
        select(AnalysisJob)
        .options(selectinload(AnalysisJob.events))
        .where(AnalysisJob.id == normalized_job_id)
    )
    return result.scalar_one_or_none()
