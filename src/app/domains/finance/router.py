from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import Buyer, DbSession, Finance, Seller
from app.domains.catalog.router import Limit, Offset
from app.domains.finance import service
from app.domains.finance.models import LedgerEntry, Payment, Settlement
from app.domains.finance.schemas import (
    LedgerOut,
    PaymentOut,
    RefundInput,
    SettlementInput,
    SettlementOut,
)
from app.domains.orders.models import ReturnRequest
from app.domains.orders.schemas import ReturnOut

router = APIRouter(tags=["Payments and finance"])


@router.post("/orders/{order_id}/payments/local", response_model=PaymentOut)
async def pay_local(order_id: UUID, db: DbSession, user: Buyer) -> Payment:
    """Development simulation. No real charge is made. Disabled outside APP_ENV=local."""
    return await service.pay_local(db, user.user_id, order_id)


@router.get("/finance/payments", response_model=list[PaymentOut])
async def payments(
    db: DbSession, user: Finance, limit: Limit = 20, offset: Offset = 0
) -> list[Payment]:
    return list(
        (
            await db.scalars(
                select(Payment)
                .order_by(Payment.created_at.desc(), Payment.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )


@router.get("/finance/returns", response_model=list[ReturnOut])
async def returns(
    db: DbSession, user: Finance, limit: Limit = 20, offset: Offset = 0
) -> list[ReturnRequest]:
    return list(
        (
            await db.scalars(
                select(ReturnRequest)
                .order_by(ReturnRequest.created_at.desc(), ReturnRequest.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )


@router.post("/finance/orders/{order_id}/refund/local", response_model=PaymentOut)
async def refund(order_id: UUID, body: RefundInput, db: DbSession, user: Finance) -> Payment:
    """Simulate a full refund after physical receipt of every returned item."""
    return await service.refund_local(db, user.user_id, order_id, body)


@router.post(
    "/finance/orders/{order_id}/settlements", response_model=SettlementOut, status_code=201
)
async def settle(order_id: UUID, body: SettlementInput, db: DbSession, user: Finance) -> Settlement:
    """Record an externally completed seller transfer. Does not initiate a payout."""
    return await service.settle(db, user.user_id, order_id, body)


@router.get("/finance/ledger", response_model=list[LedgerOut])
async def ledger(
    db: DbSession, user: Finance, limit: Limit = 20, offset: Offset = 0
) -> list[LedgerEntry]:
    return list(
        (
            await db.scalars(
                select(LedgerEntry)
                .order_by(LedgerEntry.created_at.desc(), LedgerEntry.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )


@router.get("/finance/settlements", response_model=list[SettlementOut])
async def settlements(
    db: DbSession, user: Finance, limit: Limit = 20, offset: Offset = 0
) -> list[Settlement]:
    return list(
        (
            await db.scalars(
                select(Settlement)
                .order_by(Settlement.created_at.desc(), Settlement.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )


@router.get("/seller/settlements", response_model=list[SettlementOut])
async def seller_settlements(
    db: DbSession, user: Seller, limit: Limit = 20, offset: Offset = 0
) -> list[Settlement]:
    return list(
        (
            await db.scalars(
                select(Settlement)
                .where(Settlement.seller_id == user.user_id)
                .order_by(Settlement.created_at.desc(), Settlement.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
