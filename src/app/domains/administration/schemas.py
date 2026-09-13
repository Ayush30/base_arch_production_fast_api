from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool | None = None
    seller_approved: bool | None = None


class StaffCreate(BaseModel):
    role: Literal["finance", "analytics", "admin"]
    # Staff creation is intentionally a CLI operation; this type documents allowed roles.


class ModerateProduct(BaseModel):
    blocked: bool
    reason: str = Field(min_length=5, max_length=1000)


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: UUID | None
    action: str
    resource_id: str
    details: dict[str, Any]
    created_at: datetime
