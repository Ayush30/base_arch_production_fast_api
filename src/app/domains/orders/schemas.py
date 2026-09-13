from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.shopping.schemas import AddressCreate


class Checkout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address_id: UUID
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    expected_total_minor: int = Field(gt=0, le=500_000_000_000, strict=True)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    product_id: UUID
    seller_id: UUID
    product_name: str
    sku: str
    quantity: int
    unit_price_minor: int
    fulfillment_status: str
    tracking_number: str | None
    delivered_at: datetime | None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    currency: str
    total_minor: int
    status: str
    shipping_address: AddressCreate
    expires_at: datetime
    created_at: datetime
    items: list[OrderItemOut] = []


class Fulfill(BaseModel):
    status: Literal["shipped", "delivered"]
    tracking_number: str = Field(min_length=1, max_length=100)


class ReturnCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class ReturnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    reason: str
    status: str
    created_at: datetime


class SellerFulfillment(BaseModel):
    order_id: UUID
    currency: str
    order_status: str
    shipping_address: AddressCreate
    item: OrderItemOut
