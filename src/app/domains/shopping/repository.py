from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domains.identity.models import User
from app.domains.shopping.models import Address


async def lock_buyer(db: AsyncSession, buyer_id: UUID) -> None:
    # All cart writes and checkout use the same lock, including an initially empty cart.
    await db.execute(select(User.id).where(User.id == buyer_id).with_for_update())


async def owned_address(db: AsyncSession, buyer_id: UUID, address_id: UUID) -> Address:
    address = await db.scalar(
        select(Address).where(Address.id == address_id, Address.buyer_id == buyer_id)
    )
    if address is None:
        raise NotFoundError("Address not found")
    return address
