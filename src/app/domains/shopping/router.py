from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import delete, select

from app.api.deps import Buyer, DbSession
from app.domains.catalog.router import Limit, Offset
from app.domains.shopping import service
from app.domains.shopping.models import Address, CartItem
from app.domains.shopping.repository import lock_buyer, owned_address
from app.domains.shopping.schemas import AddressCreate, AddressOut, CartOut, CartPut

router = APIRouter(tags=["Buyer shopping"])


@router.get("/addresses", response_model=list[AddressOut])
async def addresses(
    db: DbSession, user: Buyer, limit: Limit = 20, offset: Offset = 0
) -> list[Address]:
    return list(
        (
            await db.scalars(
                select(Address)
                .where(Address.buyer_id == user.user_id)
                .order_by(Address.created_at, Address.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )


@router.post("/addresses", response_model=AddressOut, status_code=201)
async def address(body: AddressCreate, db: DbSession, user: Buyer) -> Address:
    row = Address(buyer_id=user.user_id, **body.model_dump())
    db.add(row)
    await db.commit()
    return row


@router.delete("/addresses/{address_id}", status_code=204)
async def delete_address(address_id: UUID, db: DbSession, user: Buyer) -> None:
    await db.delete(await owned_address(db, user.user_id, address_id))
    await db.commit()


@router.get("/cart", response_model=list[CartOut])
async def cart(db: DbSession, user: Buyer) -> list[CartItem]:
    return list(
        (
            await db.scalars(
                select(CartItem)
                .where(CartItem.buyer_id == user.user_id)
                .order_by(CartItem.created_at, CartItem.id)
            )
        ).all()
    )


@router.put("/cart/items/{product_id}", response_model=CartOut)
async def put(product_id: UUID, body: CartPut, db: DbSession, user: Buyer) -> CartItem:
    return await service.put_item(db, user.user_id, product_id, body.quantity)


@router.delete("/cart/items/{product_id}", status_code=204)
async def remove(product_id: UUID, db: DbSession, user: Buyer) -> None:
    await lock_buyer(db, user.user_id)
    await db.execute(
        delete(CartItem).where(CartItem.buyer_id == user.user_id, CartItem.product_id == product_id)
    )
    await db.commit()
