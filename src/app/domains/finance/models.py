from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.record import Record


class Payment(Record, Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount_minor > 0", name="payment_amount"),)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), unique=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    provider: Mapped[str] = mapped_column(String(30), default="local")
    provider_reference: Mapped[str] = mapped_column(String(150), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="captured")


class LedgerEntry(Record, Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint("order_id", "kind", name="order_ledger_kind"),)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))


class Settlement(Record, Base):
    __tablename__ = "settlements"
    __table_args__ = (
        UniqueConstraint("order_id", "seller_id", name="order_seller_settlement"),
        CheckConstraint(
            "gross_minor > 0 AND commission_minor >= 0 AND net_minor >= 0",
            name="settlement_amounts",
        ),
    )
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"))
    seller_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    gross_minor: Mapped[int] = mapped_column(BigInteger)
    commission_minor: Mapped[int] = mapped_column(BigInteger)
    net_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    external_reference: Mapped[str] = mapped_column(String(150), unique=True)
