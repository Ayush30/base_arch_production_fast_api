from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domains.catalog.models import Product
from app.domains.identity.models import User


def visible_products() -> Select[tuple[Product]]:
    return (
        select(Product)
        .join(User, Product.seller_id == User.id)
        .where(
            Product.is_active.is_(True),
            Product.is_blocked.is_(False),
            User.is_active.is_(True),
            User.seller_approved.is_(True),
        )
    )


async def get_product(db: AsyncSession, product_id: UUID, *, lock: bool = False) -> Product:
    query = select(Product).where(Product.id == product_id)
    if lock:
        query = query.with_for_update()
    product = await db.scalar(query)
    if product is None:
        raise NotFoundError("Product not found")
    return product
