from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(_BaseModel):
    """All API schemas inherit from this to get camelCase on the wire."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# ── Pagination ────────────────────────────────────────────────────────────────


class PaginationMeta(CamelModel):
    total: int
    page_size: int
    next_cursor: str | None = None


class PagedResponse(CamelModel):
    data: list[Any]
    meta: dict[str, Any]


# ── ExampleItem ───────────────────────────────────────────────────────────────


class ExampleItemCreate(CamelModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ExampleItemUpdate(CamelModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    version: int = Field(..., description="Current record version for optimistic locking")


class ExampleItemResponse(CamelModel):
    id: UUID
    name: str
    description: str | None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
