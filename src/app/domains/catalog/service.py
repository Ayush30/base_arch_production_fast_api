from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError
from app.core.money import validate_currency
from app.domains.catalog.models import Product, Review
from app.domains.catalog.repository import get_product
from app.domains.catalog.schemas import ProductCreate, ProductUpdate, ReviewCreate
from app.domains.events.service import record_event


async def create(db: AsyncSession, seller_id: UUID, body: ProductCreate) -> Product:
    validate_currency(body.currency)
    product = Product(seller_id=seller_id, **body.model_dump(mode="json"))
    db.add(product)
    await db.flush()
    record_event(db, seller_id, "product.created", product.id)
    await db.commit()
    return product


async def update(
    db: AsyncSession, seller_id: UUID, product_id: UUID, body: ProductUpdate
) -> Product:
    product = await get_product(db, product_id, lock=True)
    if product.seller_id != seller_id:
        raise ForbiddenError("This product belongs to another seller")
    if product.version != body.version:
        raise ConflictError("Product changed; reload it and retry with its latest version")
    for field, value in body.model_dump(exclude={"version"}, exclude_none=True).items():
        setattr(product, field, value)
    product.version += 1
    record_event(db, seller_id, "product.updated", product.id, version=product.version)
    await db.commit()
    return product


async def review(db: AsyncSession, buyer_id: UUID, product_id: UUID, body: ReviewCreate) -> Review:
    from app.domains.orders.models import Order, OrderItem

    purchased = await db.scalar(
        select(OrderItem.id)
        .join(Order)
        .where(
            Order.buyer_id == buyer_id,
            OrderItem.product_id == product_id,
            OrderItem.fulfillment_status == "delivered",
            Order.status == "paid",
        )
    )
    if not purchased:
        raise ForbiddenError("Reviews require a delivered purchase")
    item = Review(buyer_id=buyer_id, product_id=product_id, **body.model_dump())
    db.add(item)
    await db.commit()
    return item
