"""At-least-once delivery. Kafka consumers must deduplicate by event_id."""

import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.config import settings
from app.db.session import dispose_engines, marketplace_session
from app.domains.events.models import OutboxEvent
from app.kafka.producer import publish, start_kafka_producer, stop_kafka_producer

logger = structlog.get_logger(__name__)


async def publish_batch() -> int:
    async with marketplace_session() as db:
        rows = (
            await db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.created_at, OutboxEvent.id)
                .limit(100)
                .with_for_update(skip_locked=True)
            )
        ).all()
        for event in rows:
            await publish(
                event.topic,
                {
                    "event_id": str(event.id),
                    "schema_version": 1,
                    "occurred_at": event.created_at.isoformat(),
                    **event.payload,
                },
                event.aggregate_id,
            )
            event.published_at = datetime.now(UTC)
        await db.commit()
        return len(rows)


async def main() -> None:
    if not settings.kafka_enabled:
        raise RuntimeError("Set KAFKA_ENABLED=true to run the outbox publisher")
    try:
        while await start_kafka_producer() is None:
            await asyncio.sleep(5)
        while True:
            try:
                count = await publish_batch()
                if count == 0:
                    await asyncio.sleep(2)
            except Exception:
                logger.exception("outbox_publish_failed")
                await asyncio.sleep(5)
    finally:
        await stop_kafka_producer()
        await dispose_engines()


if __name__ == "__main__":
    asyncio.run(main())
