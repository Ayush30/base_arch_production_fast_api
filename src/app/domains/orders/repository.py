from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domains.orders.models import Order, OrderItem
from app.domains.orders.schemas import OrderItemOut, OrderOut


async def get_order(db: AsyncSession, order_id: UUID, *, lock: bool = False) -> Order:
    query = select(Order).where(Order.id == order_id)
    if lock:
        query = query.with_for_update()
    order = await db.scalar(query)
    if order is None:
        raise NotFoundError("Order not found")
    return order


async def items(db: AsyncSession, order_id: UUID) -> list[OrderItem]:
    return list(
        (
            await db.scalars(
                select(OrderItem)
                .where(OrderItem.order_id == order_id)
                .order_by(OrderItem.product_id)
            )
        ).all()
    )


async def serialize(db: AsyncSession, order: Order) -> OrderOut:
    response = OrderOut.model_validate(order)
    response.items = [OrderItemOut.model_validate(item) for item in await items(db, order.id)]
    return response
