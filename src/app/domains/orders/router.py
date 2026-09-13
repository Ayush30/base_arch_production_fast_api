from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header
from sqlalchemy import select

from app.api.deps import Buyer, DbSession, Seller
from app.core.exceptions import ForbiddenError, NotFoundError
from app.domains.catalog.router import Limit, Offset
from app.domains.orders import service
from app.domains.orders.models import Order, OrderItem, ReturnRequest
from app.domains.orders.repository import get_order, serialize
from app.domains.orders.schemas import (
    Checkout,
    Fulfill,
    OrderItemOut,
    OrderOut,
    ReturnCreate,
    ReturnOut,
    SellerFulfillment,
)

router = APIRouter(tags=["Orders"])


@router.post("/checkout", response_model=OrderOut, status_code=201)
async def checkout(
    body: Checkout,
    db: DbSession,
    user: Buyer,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=128)],
) -> OrderOut:
    if not user.email_verified:
        raise ForbiddenError("Verify your email before checkout")
    return await serialize(db, await service.checkout(db, user.user_id, idempotency_key, body))


@router.get("/orders", response_model=list[OrderOut])
async def orders(
    db: DbSession, user: Buyer, limit: Limit = 20, offset: Offset = 0
) -> list[OrderOut]:
    rows = (
        await db.scalars(
            select(Order)
            .where(Order.buyer_id == user.user_id)
            .order_by(Order.created_at.desc(), Order.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [await serialize(db, row) for row in rows]


@router.get("/orders/{order_id}", response_model=OrderOut)
async def order(order_id: UUID, db: DbSession, user: Buyer) -> OrderOut:
    row = await get_order(db, order_id)
    if row.buyer_id != user.user_id:
        raise NotFoundError("Order not found")
    return await serialize(db, row)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
async def cancel(order_id: UUID, db: DbSession, user: Buyer) -> OrderOut:
    return await serialize(db, await service.cancel(db, user.user_id, order_id))


@router.post("/orders/{order_id}/returns", response_model=ReturnOut, status_code=201)
async def request_return(
    order_id: UUID, body: ReturnCreate, db: DbSession, user: Buyer
) -> ReturnRequest:
    return await service.request_return(db, user.user_id, order_id, body.reason)


@router.get("/returns", response_model=list[ReturnOut])
async def returns(
    db: DbSession, user: Buyer, limit: Limit = 20, offset: Offset = 0
) -> list[ReturnRequest]:
    return list(
        (
            await db.scalars(
                select(ReturnRequest)
                .where(ReturnRequest.buyer_id == user.user_id)
                .order_by(ReturnRequest.created_at.desc(), ReturnRequest.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )


@router.get("/seller/fulfillments", response_model=list[SellerFulfillment])
async def fulfillments(
    db: DbSession, user: Seller, limit: Limit = 20, offset: Offset = 0
) -> list[SellerFulfillment]:
    rows = (
        await db.execute(
            select(OrderItem, Order)
            .join(Order)
            .where(OrderItem.seller_id == user.user_id, Order.status == "paid")
            .order_by(OrderItem.created_at.desc(), OrderItem.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        SellerFulfillment(
            order_id=order.id,
            currency=order.currency,
            order_status=order.status,
            shipping_address=order.shipping_address,
            item=OrderItemOut.model_validate(line),
        )
        for line, order in rows
    ]


@router.post("/seller/fulfillments/{item_id}", response_model=OrderItemOut)
async def fulfill(item_id: UUID, body: Fulfill, db: DbSession, user: Seller) -> OrderItem:
    return await service.fulfill(db, user.user_id, item_id, body)
