from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.record import Record


class Product(Record, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("seller_id", "sku", name="seller_sku"),
        CheckConstraint("price_minor > 0 AND stock >= 0", name="product_amounts"),
    )
    seller_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    sku: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), index=True)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Review(Record, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("buyer_id", "product_id", name="buyer_product_review"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="review_rating"),
    )
    buyer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(2000), default="")
