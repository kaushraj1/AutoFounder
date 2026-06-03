"""Async database engine and session factory.

The engine is created lazily (no connection is opened at import), so importing this module
is safe even when no database is reachable (e.g. during unit tests that never touch the DB).
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(_settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a request-scoped async session."""
    async with SessionLocal() as session:
        yield session
