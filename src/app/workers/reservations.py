"""Release inventory for abandoned unpaid checkout reservations."""

import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.db.session import dispose_engines, marketplace_session
from app.domains.events.service import record_event
from app.domains.orders.models import Order
from app.domains.orders.service import restock

logger = structlog.get_logger(__name__)


async def expire_batch() -> int:
    async with marketplace_session() as db:
        # One order per transaction keeps product locks globally ordered.
        order = await db.scalar(
            select(Order)
            .where(Order.status == "pending", Order.expires_at <= datetime.now(UTC))
            .order_by(Order.expires_at, Order.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if order is None:
            return 0
        await restock(db, order)
        order.status = "cancelled"
        record_event(db, None, "order.expired", order.id)
        await db.commit()
        return 1


async def main() -> None:
    try:
        while True:
            try:
                if await expire_batch() == 0:
                    await asyncio.sleep(5)
            except Exception:
                logger.exception("reservation_expiry_failed")
                await asyncio.sleep(5)
    finally:
        await dispose_engines()


if __name__ == "__main__":
    asyncio.run(main())
