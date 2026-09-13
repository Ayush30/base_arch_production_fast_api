from __future__ import annotations

from typing import TYPE_CHECKING

from uuid_extensions import uuid7  # type: ignore[import-untyped]

from app.core.exceptions import OptimisticLockError
from app.core.messages import ExampleMsg
from app.domains.example.models import ExampleItem
from app.domains.example.schemas import ExampleItemCreate, ExampleItemResponse, ExampleItemUpdate

if TYPE_CHECKING:
    from uuid import UUID

    from app.domains.example.repository import ExampleItemRepository


class ExampleItemService:
    def __init__(self, repo: ExampleItemRepository, actor_id: UUID) -> None:
        self._repo = repo
        self._actor_id = actor_id

    async def get(self, item_id: UUID) -> ExampleItemResponse:
        item = await self._repo.get_by_id(item_id)
        return ExampleItemResponse.model_validate(item)

    async def list(self, limit: int = 50, offset: int = 0) -> list[ExampleItemResponse]:
        items = await self._repo.list_active(limit=limit, offset=offset)
        return [ExampleItemResponse.model_validate(i) for i in items]

    async def create(self, data: ExampleItemCreate) -> ExampleItemResponse:
        item = ExampleItem(
            id=uuid7(),
            name=data.name,
            description=data.description,
            created_by=self._actor_id,
            updated_by=self._actor_id,
        )
        created = await self._repo.create(item)
        return ExampleItemResponse.model_validate(created)

    async def update(self, item_id: UUID, data: ExampleItemUpdate) -> ExampleItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item.version != data.version:
            raise OptimisticLockError(
                ExampleMsg.VERSION_MISMATCH,
                expected_version=item.version,
                actual_version=data.version,
            )
        if data.name is not None:
            item.name = data.name
        if data.description is not None:
            item.description = data.description
        item.version += 1
        item.updated_by = self._actor_id
        await self._repo.create(item)  # flush via create (already in session)
        return ExampleItemResponse.model_validate(item)

    async def delete(self, item_id: UUID) -> None:
        item = await self._repo.get_by_id(item_id)
        await self._repo.delete(item)
