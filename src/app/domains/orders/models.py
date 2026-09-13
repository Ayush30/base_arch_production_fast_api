from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.record import Record


class Order(Record, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("buyer_id", "idempotency_key", name="buyer_checkout_key"),
        CheckConstraint("total_minor > 0", name="order_total"),
        CheckConstraint("status IN ('pending','paid','cancelled','refunded')", name="order_status"),
    )
    buyer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(3))
    total_minor: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    shipping_address: Mapped[dict[str, Any]] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class OrderItem(Record, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0 AND unit_price_minor > 0 AND commission_minor >= 0",
            name="order_item_amounts",
        ),
        CheckConstraint(
            "fulfillment_status IN ('unfulfilled','shipped','delivered')", name="fulfillment_state"
        ),
    )
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    seller_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    product_name: Mapped[str] = mapped_column(String(200))
    sku: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_minor: Mapped[int] = mapped_column(Integer)
    commission_minor: Mapped[int] = mapped_column(BigInteger)
    fulfillment_status: Mapped[str] = mapped_column(String(20), default="unfulfilled")
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReturnRequest(Record, Base):
    __tablename__ = "return_requests"
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), unique=True)
    buyer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default="requested")
