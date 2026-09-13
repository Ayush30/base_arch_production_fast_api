import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.money import commission, validate_currency
from app.domains.catalog.repository import get_product
from app.domains.events.service import record_event
from app.domains.identity.models import User
from app.domains.orders.models import Order, OrderItem, ReturnRequest
from app.domains.orders.repository import get_order, items
from app.domains.orders.schemas import Checkout, Fulfill
from app.domains.shopping.models import CartItem
from app.domains.shopping.repository import lock_buyer, owned_address
from app.domains.shopping.schemas import AddressCreate

RETURN_DAYS = 14


async def checkout(db: AsyncSession, buyer_id: UUID, key: str, body: Checkout) -> Order:
    validate_currency(body.currency)
    fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    await lock_buyer(db, buyer_id)
    existing = await db.scalar(
        select(Order).where(Order.buyer_id == buyer_id, Order.idempotency_key == key)
    )
    if existing:
        if existing.request_hash != fingerprint:
            raise ConflictError("Idempotency key was already used with different checkout details")
        return existing
    address = await owned_address(db, buyer_id, body.address_id)
    cart = list(
        (
            await db.scalars(
                select(CartItem).where(CartItem.buyer_id == buyer_id).order_by(CartItem.product_id)
            )
        ).all()
    )
    if not cart:
        raise ValidationError("Cart is empty")
    order = Order(
        buyer_id=buyer_id,
        idempotency_key=key,
        request_hash=fingerprint,
        currency=body.currency,
        total_minor=body.expected_total_minor,
        shipping_address=AddressCreate.model_validate(address, from_attributes=True).model_dump(),
        expires_at=datetime.now(UTC) + timedelta(minutes=settings.checkout_expiry_minutes),
    )
    db.add(order)
    await db.flush()
    total = 0
    for line in cart:
        # Always acquire product locks in UUID order to avoid cross-cart deadlocks.
        product = await get_product(db, line.product_id, lock=True)
        seller = await db.get(User, product.seller_id)
        if (
            not product.is_active
            or product.is_blocked
            or not seller
            or not seller.is_active
            or not seller.seller_approved
        ):
            raise ConflictError("A product is no longer available")
        if product.currency != body.currency:
            raise ValidationError("Every cart product must use the checkout currency")
        if product.stock < line.quantity:
            raise ConflictError("Insufficient stock; refresh your cart")
        product.stock -= line.quantity
        product.version += 1
        subtotal = product.price_minor * line.quantity
        total += subtotal
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                seller_id=product.seller_id,
                product_name=product.name,
                sku=product.sku,
                quantity=line.quantity,
                unit_price_minor=product.price_minor,
                commission_minor=commission(subtotal, settings.commission_bps),
            )
        )
    if total != body.expected_total_minor:
        raise ConflictError("Prices changed; review the cart total before checking out")
    await db.execute(delete(CartItem).where(CartItem.buyer_id == buyer_id))
    record_event(
        db, buyer_id, "order.created", order.id, currency=order.currency, total_minor=total
    )
    await db.commit()
    return order


async def restock(db: AsyncSession, order: Order) -> None:
    for line in await items(db, order.id):
        product = await get_product(db, line.product_id, lock=True)
        product.stock += line.quantity
        product.version += 1


async def cancel(db: AsyncSession, buyer_id: UUID, order_id: UUID) -> Order:
    order = await get_order(db, order_id, lock=True)
    if order.buyer_id != buyer_id:
        raise NotFoundError("Order not found")
    if order.status == "cancelled":
        return order
    if order.status != "pending":
        raise ConflictError("Only unpaid orders can be cancelled")
    await restock(db, order)
    order.status = "cancelled"
    record_event(db, buyer_id, "order.cancelled", order.id)
    await db.commit()
    return order


async def fulfill(db: AsyncSession, seller_id: UUID, item_id: UUID, body: Fulfill) -> OrderItem:
    line = await db.get(OrderItem, item_id)
    if not line or line.seller_id != seller_id:
        raise NotFoundError("Order item not found")
    order = await get_order(db, line.order_id, lock=True)
    await db.refresh(line)
    if order.status != "paid":
        raise ConflictError("Only paid orders can be fulfilled")
    if line.fulfillment_status == body.status:
        if line.tracking_number != body.tracking_number:
            raise ConflictError("Tracking number differs from the existing shipment")
        return line
    required = "unfulfilled" if body.status == "shipped" else "shipped"
    if line.fulfillment_status != required:
        raise ConflictError("Invalid fulfillment transition")
    if body.status == "delivered" and line.tracking_number != body.tracking_number:
        raise ConflictError("Tracking number must match the shipment")
    line.fulfillment_status = body.status
    line.tracking_number = body.tracking_number
    if body.status == "delivered":
        line.delivered_at = datetime.now(UTC)
    record_event(db, seller_id, f"shipment.{body.status}", order.id, item_id=str(line.id))
    await db.commit()
    return line


async def request_return(
    db: AsyncSession, buyer_id: UUID, order_id: UUID, reason: str
) -> ReturnRequest:
    order = await get_order(db, order_id, lock=True)
    if order.buyer_id != buyer_id:
        raise NotFoundError("Order not found")
    existing = await db.scalar(select(ReturnRequest).where(ReturnRequest.order_id == order.id))
    if existing:
        return existing
    lines = await items(db, order.id)
    cutoff = datetime.now(UTC) - timedelta(days=RETURN_DAYS)
    if order.status != "paid" or any(
        line.fulfillment_status != "delivered"
        or line.delivered_at is None
        or line.delivered_at < cutoff
        for line in lines
    ):
        raise ConflictError(
            "Full-order returns require all items delivered within the last 14 days"
        )
    request = ReturnRequest(order_id=order.id, buyer_id=buyer_id, reason=reason)
    db.add(request)
    record_event(db, buyer_id, "return.requested", order.id)
    await db.commit()
    return request
