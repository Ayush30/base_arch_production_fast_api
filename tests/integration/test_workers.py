from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.domains.events.models import OutboxEvent
from app.domains.orders.models import Order
from app.workers.outbox import publish_batch
from app.workers.reservations import expire_batch
from tests.integration.test_marketplace import checkout, prepare, product


@asynccontextmanager
async def session_scope(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def test_expiry_restocks_once(
    client: AsyncClient, accounts: dict, db_session: AsyncSession, test_engine: AsyncEngine
) -> None:
    p = await product(client, accounts)
    order = (await checkout(client, accounts, await prepare(client, accounts, [p]))).json()
    row = await db_session.get(Order, UUID(order["id"]))
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()
    assert (
        await client.post(
            f"/api/v1/orders/{order['id']}/payments/local", headers=accounts["buyer"]["headers"]
        )
    ).status_code == 409
    with patch("app.workers.reservations.marketplace_session", lambda: session_scope(test_engine)):
        assert await expire_batch() == 1
        assert await expire_batch() == 0
    assert (await client.get(f"/api/v1/products/{p['id']}")).json()["stock"] == 10


async def test_outbox_failure_is_retryable(
    db_session: AsyncSession, test_engine: AsyncEngine
) -> None:
    event = OutboxEvent(
        topic="marketplace.events", aggregate_id="test", payload={"type": "test.event"}
    )
    db_session.add(event)
    await db_session.commit()
    with patch("app.workers.outbox.marketplace_session", lambda: session_scope(test_engine)):
        with (
            patch(
                "app.workers.outbox.publish", new=AsyncMock(side_effect=RuntimeError("broker down"))
            ),
            pytest.raises(RuntimeError),
        ):
            await publish_batch()
        await db_session.refresh(event)
        assert event.published_at is None
        # Close the read transaction before the worker updates it.
        await db_session.commit()
        with patch("app.workers.outbox.publish", new=AsyncMock()) as publish:
            assert await publish_batch() == 1
            assert publish.call_args.args[1]["event_id"] == str(event.id)
            assert await publish_batch() == 0
    result = await db_session.scalar(
        select(OutboxEvent)
        .where(OutboxEvent.id == event.id)
        .execution_options(populate_existing=True)
    )
    assert result.published_at is not None
