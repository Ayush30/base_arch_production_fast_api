from __future__ import annotations

import os
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.domains.identity.models import User
from app.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
    from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def test_settings(tmp_path_factory: pytest.TempPathFactory) -> Generator[None, None, None]:
    previous = settings.model_copy()
    keys: Path = tmp_path_factory.mktemp("keys")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    (keys / "private.pem").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    (keys / "public.pem").write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )
    settings.jwt_private_key_path = str(keys / "private.pem")
    settings.jwt_public_key_path = str(keys / "public.pem")
    settings.rate_limit_enabled = False
    settings.allowed_hosts = ["test", "testserver", "localhost", "127.0.0.1"]
    settings.app_env = "local"
    settings.local_payments_enabled = True
    settings.local_email_tokens_enabled = True
    yield
    for name in type(settings).model_fields:
        setattr(settings, name, getattr(previous, name))


@pytest.fixture(scope="session")
def db_url() -> Generator[str, None, None]:
    configured = os.getenv("TEST_DATABASE_URL")
    if configured:
        yield configured
    else:
        with PostgresContainer("postgres:16-alpine") as pg:
            yield pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")


@pytest_asyncio.fixture
async def test_engine(db_url: str) -> AsyncGenerator[AsyncEngine, None]:
    schema = "test_" + uuid4().hex
    engine = create_async_engine(db_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        await conn.execution_options(schema_translate_map={None: schema})
        await conn.run_sync(Base.metadata.create_all)
    scoped = engine.execution_options(schema_translate_map={None: schema})
    yield scoped
    async with engine.begin() as conn:
        await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def database() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSession(test_engine, expire_on_commit=False) as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


PASSWORD = "Test-password-2026!"


@pytest_asyncio.fixture
async def accounts(db_session: AsyncSession, client: AsyncClient) -> dict:
    result = {}
    password_hash = hash_password(PASSWORD)
    for role in ("buyer", "seller", "finance", "analytics", "admin", "buyer2", "seller2"):
        user = User(
            email=f"{role}@example.com",
            name=role,
            role=role.rstrip("2"),
            password_hash=password_hash,
            email_verified=True,
            seller_approved=True,
        )
        db_session.add(user)
        await db_session.commit()
        response = await client.post(
            "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        result[role] = {
            "id": str(user.id),
            "headers": {"Authorization": "Bearer " + response.json()["access_token"]},
            "tokens": response.json(),
        }
    return result
