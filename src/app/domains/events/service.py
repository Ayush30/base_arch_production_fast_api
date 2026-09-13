from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.events.models import AuditLog, OutboxEvent


def record_event(
    db: AsyncSession, actor: UUID | None, action: str, resource_id: UUID, **details: Any
) -> None:
    """Persist audit and event in the business transaction. Never include secrets/addresses."""
    db.add(AuditLog(actor_id=actor, action=action, resource_id=str(resource_id), details=details))
    db.add(
        OutboxEvent(
            topic="marketplace.events",
            aggregate_id=str(resource_id),
            payload={"type": action, "resource_id": str(resource_id), **details},
        )
    )
