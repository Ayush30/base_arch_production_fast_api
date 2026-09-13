from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import AuthUser, DbSession
from app.domains.example.repository import ExampleItemRepository
from app.domains.example.schemas import ExampleItemCreate, ExampleItemResponse, ExampleItemUpdate
from app.domains.example.service import ExampleItemService

router = APIRouter(prefix="/examples", tags=["examples"])


def _service(db: DbSession, user: AuthUser) -> ExampleItemService:
    return ExampleItemService(repo=ExampleItemRepository(db), actor_id=user.user_id)


@router.get(
    "",
    response_model=list[ExampleItemResponse],
    summary="List example items",
    operation_id="example_list",
)
async def list_items(
    db: DbSession,
    user: AuthUser,
    limit: int = 50,
    offset: int = 0,
) -> list[ExampleItemResponse]:
    return await _service(db, user).list(limit=limit, offset=offset)


@router.post(
    "",
    response_model=ExampleItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an example item",
    operation_id="example_create",
)
async def create_item(
    body: ExampleItemCreate,
    db: DbSession,
    user: AuthUser,
) -> ExampleItemResponse:
    return await _service(db, user).create(body)


@router.get(
    "/{item_id}",
    response_model=ExampleItemResponse,
    summary="Get a single example item",
    operation_id="example_get",
)
async def get_item(
    item_id: UUID,
    db: DbSession,
    user: AuthUser,
) -> ExampleItemResponse:
    return await _service(db, user).get(item_id)


@router.patch(
    "/{item_id}",
    response_model=ExampleItemResponse,
    summary="Update an example item",
    operation_id="example_update",
)
async def update_item(
    item_id: UUID,
    body: ExampleItemUpdate,
    db: DbSession,
    user: AuthUser,
) -> ExampleItemResponse:
    return await _service(db, user).update(item_id, body)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an example item",
    operation_id="example_delete",
)
async def delete_item(
    item_id: UUID,
    db: DbSession,
    user: AuthUser,
) -> None:
    await _service(db, user).delete(item_id)
