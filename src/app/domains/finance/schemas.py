from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    amount_minor: int
    currency: str
    provider: str
    provider_reference: str
    status: str
    created_at: datetime


class RefundInput(BaseModel):
    goods_received: bool
    reason: str = Field(min_length=5, max_length=1000)


class SettlementInput(BaseModel):
    seller_id: UUID
    external_reference: str = Field(min_length=8, max_length=150)


class SettlementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    seller_id: UUID
    gross_minor: int
    commission_minor: int
    net_minor: int
    currency: str
    external_reference: str
    created_at: datetime


class LedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    kind: str
    amount_minor: int
    currency: str
    created_at: datetime
