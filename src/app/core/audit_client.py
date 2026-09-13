from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.core.config import settings
from app.kafka.constants import KafkaTopics
from app.kafka.producer import publish

if TYPE_CHECKING:
    from uuid import UUID

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


async def emit_audit_event(
    *,
    actor_type: str,
    action: str,
    status: str,
    actor_id: UUID | None = None,
    actor_name: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    resource_name: str | None = None,
    ip_address: str | None = None,
    extra: dict[str, object] | None = None,
) -> None:
    """Publish an audit event to Kafka, consumed by audit-service.

    Never raises — a failed publish is logged and swallowed so audit delivery
    can never break the caller's request. Requires start_kafka_producer() to
    have run (see main.py's lifespan).
    """
    event = {
        "service_name": settings.app_name,
        "actor_type": actor_type,
        "actor_id": str(actor_id) if actor_id else None,
        "actor_name": actor_name,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": resource_name,
        "action": action,
        "status": status,
        "ip_address": ip_address,
        "extra": extra,
    }
    try:
        await publish(
            KafkaTopics.Audit.USER_ACTIVITY, event, key=str(actor_id) if actor_id else None
        )
    except Exception as exc:
        logger.warning("audit_event_publish_failed", error=str(exc), event=event)
