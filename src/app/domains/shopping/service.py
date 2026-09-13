from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.domains.catalog.models import Product
from app.domains.catalog.repository import visible_products
from app.domains.shopping.models import CartItem
from app.domains.shopping.repository import lock_buyer


async def put_item(db: AsyncSession, buyer_id: UUID, product_id: UUID, quantity: int) -> CartItem:
    await lock_buyer(db, buyer_id)
    product = await db.scalar(visible_products().where(Product.id == product_id))
    if not product:
        raise NotFoundError("Product not found")
    if quantity > product.stock:
        raise ValidationError("Requested quantity exceeds available stock")
    item = await db.scalar(
        select(CartItem).where(CartItem.buyer_id == buyer_id, CartItem.product_id == product_id)
    )
    if item is None:
        count = len(
            (await db.scalars(select(CartItem.id).where(CartItem.buyer_id == buyer_id))).all()
        )
        if count >= 50:
            raise ValidationError("Cart is limited to 50 distinct products")
        item = CartItem(buyer_id=buyer_id, product_id=product_id, quantity=quantity)
        db.add(item)
    else:
        item.quantity = quantity
    await db.commit()
    return item
