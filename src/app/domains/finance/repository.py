from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.finance.models import Payment


async def payment_for_order(db: AsyncSession, order_id: UUID) -> Payment | None:
    return (
        await db.execute(select(Payment).where(Payment.order_id == order_id))
    ).scalar_one_or_none()
