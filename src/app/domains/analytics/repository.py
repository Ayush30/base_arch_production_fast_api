from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.schemas import CurrencySales, ProductSales, SellerSales
from app.domains.orders.models import Order, OrderItem


async def sales(db: AsyncSession, seller_id: UUID | None = None) -> list[CurrencySales]:
    query = (
        select(
            Order.currency,
            func.count(func.distinct(Order.id)),
            func.sum(OrderItem.quantity * OrderItem.unit_price_minor),
            func.sum(OrderItem.commission_minor),
        )
        .join(OrderItem)
        .where(Order.status == "paid")
    )
    if seller_id:
        query = query.where(OrderItem.seller_id == seller_id)
    rows = (await db.execute(query.group_by(Order.currency).order_by(Order.currency))).all()
    return [
        CurrencySales(currency=c, paid_orders=n, gross_minor=g, commission_minor=f)
        for c, n, g, f in rows
    ]


async def product_sales(db: AsyncSession, limit: int, offset: int) -> list[ProductSales]:
    gross = func.sum(OrderItem.quantity * OrderItem.unit_price_minor)
    rows = (
        await db.execute(
            select(OrderItem.product_id, Order.currency, func.sum(OrderItem.quantity), gross)
            .join(Order)
            .where(Order.status == "paid")
            .group_by(OrderItem.product_id, Order.currency)
            .order_by(Order.currency, gross.desc(), OrderItem.product_id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [ProductSales(product_id=p, currency=c, units=n, gross_minor=g) for p, c, n, g in rows]


async def seller_sales(db: AsyncSession, limit: int, offset: int) -> list[SellerSales]:
    gross = func.sum(OrderItem.quantity * OrderItem.unit_price_minor)
    rows = (
        await db.execute(
            select(
                OrderItem.seller_id,
                Order.currency,
                func.sum(OrderItem.quantity),
                gross,
                func.sum(OrderItem.commission_minor),
            )
            .join(Order)
            .where(Order.status == "paid")
            .group_by(OrderItem.seller_id, Order.currency)
            .order_by(Order.currency, gross.desc(), OrderItem.seller_id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        SellerSales(seller_id=s, currency=c, units=n, gross_minor=g, commission_minor=f)
        for s, c, n, g, f in rows
    ]
