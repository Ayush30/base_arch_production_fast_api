from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(postgres_container: PostgresContainer) -> str:
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    user = postgres_container.username
    password = postgres_container.password
    db = postgres_container.dbname
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


@pytest_asyncio.fixture(scope="session")
async def test_engine(db_url: str) -> Any:
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


FAKE_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
FAKE_TENANT_ID = UUID("00000000-0000-0000-0000-000000000002")


class _FakeUser:
    user_id = FAKE_USER_ID
    tenant_id = FAKE_TENANT_ID
    tenant_slug = "test"
    roles: list[str] = ["admin"]

    def has_role(self, role: str) -> bool:
        return role in self.roles


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _FakeUser()
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
