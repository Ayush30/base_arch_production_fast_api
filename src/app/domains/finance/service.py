from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.events.service import record_event
from app.domains.finance.models import LedgerEntry, Payment, Settlement
from app.domains.finance.repository import payment_for_order
from app.domains.finance.schemas import RefundInput, SettlementInput
from app.domains.orders.models import ReturnRequest
from app.domains.orders.repository import get_order, items
from app.domains.orders.service import RETURN_DAYS, restock


def require_local_payments() -> None:
    if not settings.local_payments_enabled or not settings.is_local:
        raise NotFoundError("Local payment simulation is unavailable")


async def pay_local(db: AsyncSession, buyer_id: UUID, order_id: UUID) -> Payment:
    require_local_payments()
    order = await get_order(db, order_id, lock=True)
    if order.buyer_id != buyer_id:
        raise NotFoundError("Order not found")
    existing = await payment_for_order(db, order_id)
    if existing:
        return existing
    if order.status != "pending" or order.expires_at <= datetime.now(UTC):
        raise ConflictError("Order cannot be paid; it is cancelled or its reservation expired")
    payment = Payment(
        order_id=order.id,
        amount_minor=order.total_minor,
        currency=order.currency,
        provider_reference=f"local:{order.id}",
    )
    db.add(payment)
    db.add(
        LedgerEntry(
            order_id=order.id,
            kind="capture",
            amount_minor=order.total_minor,
            currency=order.currency,
        )
    )
    order.status = "paid"
    record_event(
        db,
        buyer_id,
        "payment.captured",
        order.id,
        currency=order.currency,
        amount_minor=order.total_minor,
    )
    await db.commit()
    return payment


async def refund_local(
    db: AsyncSession, actor_id: UUID, order_id: UUID, body: RefundInput
) -> Payment:
    require_local_payments()
    order = await get_order(db, order_id, lock=True)
    payment = await payment_for_order(db, order_id)
    if not payment:
        raise NotFoundError("Payment not found")
    if order.status == "refunded":
        return payment
    request = await db.scalar(select(ReturnRequest).where(ReturnRequest.order_id == order.id))
    settled = await db.scalar(select(Settlement.id).where(Settlement.order_id == order.id))
    if order.status != "paid" or not request or request.status != "requested" or settled:
        raise ConflictError("Refund requires an unsettled paid order with an open return request")
    if not body.goods_received:
        raise ValidationError("Confirm all returned goods were received before refunding")
    await restock(db, order)
    order.status = "refunded"
    payment.status = "refunded"
    request.status = "refunded"
    db.add(
        LedgerEntry(
            order_id=order.id,
            kind="refund",
            amount_minor=-order.total_minor,
            currency=order.currency,
        )
    )
    record_event(db, actor_id, "payment.refunded", order.id, reason=body.reason)
    await db.commit()
    return payment


async def settle(
    db: AsyncSession, actor_id: UUID, order_id: UUID, body: SettlementInput
) -> Settlement:
    # Records a manually verified transfer; this endpoint never sends money.
    order = await get_order(db, order_id, lock=True)
    existing = await db.scalar(
        select(Settlement).where(
            Settlement.order_id == order.id, Settlement.seller_id == body.seller_id
        )
    )
    if existing:
        if existing.external_reference != body.external_reference:
            raise ConflictError("Settlement already recorded with another reference")
        return existing
    request = await db.scalar(select(ReturnRequest.id).where(ReturnRequest.order_id == order.id))
    lines = await items(db, order.id)
    cutoff = datetime.now(UTC) - timedelta(days=RETURN_DAYS)
    if (
        order.status != "paid"
        or request
        or any(line.delivered_at is None or line.delivered_at > cutoff for line in lines)
    ):
        raise ConflictError(
            "Settle only delivered orders after the 14-day return window, with no return request"
        )
    seller_lines = [line for line in lines if line.seller_id == body.seller_id]
    if not seller_lines:
        raise NotFoundError("Seller has no items in this order")
    gross = sum(line.unit_price_minor * line.quantity for line in seller_lines)
    fee = sum(line.commission_minor for line in seller_lines)
    settlement = Settlement(
        order_id=order.id,
        seller_id=body.seller_id,
        gross_minor=gross,
        commission_minor=fee,
        net_minor=gross - fee,
        currency=order.currency,
        external_reference=body.external_reference,
    )
    db.add(settlement)
    record_event(
        db,
        actor_id,
        "settlement.recorded",
        order.id,
        seller_id=str(body.seller_id),
        net_minor=gross - fee,
    )
    await db.commit()
    return settlement
