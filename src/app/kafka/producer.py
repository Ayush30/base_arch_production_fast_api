from __future__ import annotations

import json
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer

from app.core.config import settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_producer: AIOKafkaProducer | None = None


async def start_kafka_producer() -> AIOKafkaProducer | None:
    global _producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8") if key is not None else None,
    )
    try:
        await producer.start()
    except Exception as exc:
        logger.error(
            "kafka_producer_start_failed",
            error=str(exc),
            bootstrap_servers=settings.kafka_bootstrap_servers,
        )
        _producer = None
        return None

    _producer = producer
    return _producer


async def stop_kafka_producer() -> None:
    global _producer
    if _producer is not None:
        try:
            await _producer.stop()
        except Exception as exc:
            logger.warning("kafka_producer_stop_failed", error=str(exc))
        finally:
            _producer = None


async def publish(topic: str, value: dict[str, Any], key: str | None = None) -> None:
    """Publish an event to Kafka. Requires start_kafka_producer() to have run."""
    if _producer is None:
        raise RuntimeError("Kafka producer is not started")

    await _producer.send_and_wait(topic, value=value, key=key)
    logger.debug("kafka_message_produced", topic=topic, key=key)
