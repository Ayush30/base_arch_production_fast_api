from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.core.messages import ExampleMsg
from app.domains.example.models import ExampleItem

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class ExampleItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: UUID) -> ExampleItem:
        result = await self._session.execute(
            select(ExampleItem).where(
                ExampleItem.id == item_id,
                ExampleItem.deleted_at.is_(None),
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise NotFoundError(ExampleMsg.NOT_FOUND, item_id=item_id)
        return item

    async def list_active(self, limit: int = 50, offset: int = 0) -> list[ExampleItem]:
        result = await self._session.execute(
            select(ExampleItem)
            .where(ExampleItem.deleted_at.is_(None))
            .order_by(ExampleItem.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, item: ExampleItem) -> ExampleItem:
        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)
        return item

    async def delete(self, item: ExampleItem) -> None:
        """Soft-delete: set deleted_at, never hard-delete tenant data."""
        from datetime import UTC, datetime

        item.deleted_at = datetime.now(UTC)
        await self._session.flush()
