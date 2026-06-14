"""Alembic migration environment (async).

The database URL comes from ``app.core.config`` so migrations use the same configuration
as the application. Importing ``app.models`` registers every model on ``Base.metadata``.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import get_settings
from app.db.base import Base
import app.models  # noqa: F401  (import for side effect: register models on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Read URL directly from settings (avoids ConfigParser % interpolation issues).
_DB_URL = get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations without a DB-API connection (emits SQL)."""
    context.configure(
        url=_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations with an async engine."""
    from sqlalchemy.ext.asyncio import create_async_engine

    connectable = create_async_engine(_DB_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
