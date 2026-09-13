from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.core.exceptions import OptimisticLockError
from app.domains.example.models import ExampleItem
from app.domains.example.schemas import ExampleItemCreate, ExampleItemUpdate
from app.domains.example.service import ExampleItemService

ACTOR_ID = UUID("00000000-0000-0000-0000-000000000001")
ITEM_ID = UUID("00000000-0000-0000-0000-000000000010")

_now = datetime.now(UTC)


def _make_item(**kwargs: object) -> ExampleItem:
    item = ExampleItem()
    item.id = ITEM_ID
    item.name = "Test"
    item.description = None
    item.version = 1
    item.created_at = _now
    item.updated_at = _now
    item.created_by = ACTOR_ID
    item.updated_by = ACTOR_ID
    item.deleted_at = None
    for k, v in kwargs.items():
        setattr(item, k, v)
    return item


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> ExampleItemService:
    return ExampleItemService(repo=repo, actor_id=ACTOR_ID)


@pytest.mark.asyncio
async def test_create_delegates_to_repo(service: ExampleItemService, repo: AsyncMock) -> None:
    repo.create.return_value = _make_item(name="Widget")
    result = await service.create(ExampleItemCreate(name="Widget"))
    assert result.name == "Widget"
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_version_mismatch_raises(service: ExampleItemService, repo: AsyncMock) -> None:
    repo.get_by_id.return_value = _make_item(version=2)
    with pytest.raises(OptimisticLockError):
        await service.update(ITEM_ID, ExampleItemUpdate(name="New", version=1))


@pytest.mark.asyncio
async def test_delete_calls_soft_delete(service: ExampleItemService, repo: AsyncMock) -> None:
    repo.get_by_id.return_value = _make_item()
    await service.delete(ITEM_ID)
    repo.delete.assert_awaited_once()
