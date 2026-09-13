from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.tenancy import current_schema

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


def _make_engine(
    url: str,
    *,
    pool_size: int,
    max_overflow: int,
    pool_timeout: int,
    pool_recycle: int,
) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,
        echo=settings.debug,
    )


# Write engine — always points to the primary database.
engine = _make_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
)

# Read engine — separate pool when a replica URL is configured; aliases the
# primary engine otherwise, so no behavior changes when no replica is set.
_replica_url = settings.database_read_replica_url
read_engine: AsyncEngine = (
    _make_engine(
        _replica_url,
        pool_size=settings.db_read_pool_size,
        max_overflow=settings.db_read_max_overflow,
        pool_timeout=settings.db_read_pool_timeout,
        pool_recycle=settings.db_read_pool_recycle,
    )
    if _replica_url
    else engine
)

_write_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
_read_factory = async_sessionmaker(read_engine, expire_on_commit=False, class_=AsyncSession)

# Kept for backwards compatibility with code that imported async_session_factory directly.
async_session_factory = _write_factory


async def dispose_engines() -> None:
    """Dispose all engine pools. Call from app lifespan shutdown."""
    await engine.dispose()
    if read_engine is not engine:
        await read_engine.dispose()


@asynccontextmanager
async def shared_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager yielding a write session pinned to the shared schema.

    Use this for operations that do not belong to any tenant, such as seeding,
    provisioning, or background jobs where no JWT tenant context exists.
    """
    translate_map: dict[str | None, str] = {
        None: settings.shared_schema,
        "shared": settings.shared_schema,
    }
    async with engine.connect() as conn:
        await conn.execution_options(schema_translate_map=translate_map)
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _tenant_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    tenant_schema = current_schema()
    translate_map = {None: tenant_schema, "shared": settings.shared_schema}

    async with db_engine.connect() as conn:
        await conn.execution_options(schema_translate_map=translate_map)
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession scoped to the current tenant schema (write engine).

    Use for route handlers that perform writes or need primary-read consistency.
    """
    async for session in _tenant_session(engine):
        yield session


async def get_read_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession scoped to the current tenant schema (read engine).

    Routes to the read replica when DATABASE_READ_REPLICA_URL is set; falls
    back to the primary when no replica is configured. Use for read-only routes.
    """
    async for session in _tenant_session(read_engine):
        yield session


@asynccontextmanager
async def marketplace_session() -> AsyncGenerator[AsyncSession, None]:
    """Single marketplace schema; seller isolation is enforced by ownership queries.

    Commit in the route/service before returning mutations when a commit failure
    must be visible to the client. This final commit also covers read-only routes.
    """
    async with shared_session() as session:
        yield session
