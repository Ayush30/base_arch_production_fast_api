from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import Buyer, DbSession, Seller
from app.core.exceptions import NotFoundError
from app.domains.catalog import service
from app.domains.catalog.models import Product, Review
from app.domains.catalog.repository import visible_products
from app.domains.catalog.schemas import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ReviewCreate,
    ReviewOut,
)

router = APIRouter(tags=["Catalog"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=100000)]


@router.get("/products", response_model=list[ProductOut])
async def products(
    db: DbSession,
    limit: Limit = 20,
    offset: Offset = 0,
    search: Annotated[str | None, Query(max_length=100)] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    currency: Annotated[str | None, Query(pattern="^[A-Z]{3}$")] = None,
) -> list[Product]:
    query = visible_products()
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Product.category == category)
    if currency:
        query = query.where(Product.currency == currency)
    return list(
        (
            await db.scalars(
                query.order_by(Product.created_at.desc(), Product.id).limit(limit).offset(offset)
            )
        ).all()
    )


@router.get("/products/{product_id}", response_model=ProductOut)
async def product(product_id: UUID, db: DbSession) -> Product:
    result = await db.scalar(visible_products().where(Product.id == product_id))
    if result is None:
        raise NotFoundError("Product not found")
    return result


@router.get("/seller/products", response_model=list[ProductOut])
async def seller_products(
    db: DbSession, user: Seller, limit: Limit = 20, offset: Offset = 0
) -> list[Product]:
    return list(
        (
            await db.scalars(
                select(Product)
                .where(Product.seller_id == user.user_id)
                .order_by(Product.created_at.desc(), Product.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )


@router.post("/seller/products", response_model=ProductOut, status_code=201)
async def create(body: ProductCreate, db: DbSession, user: Seller) -> Product:
    return await service.create(db, user.user_id, body)


@router.patch("/seller/products/{product_id}", response_model=ProductOut)
async def update(product_id: UUID, body: ProductUpdate, db: DbSession, user: Seller) -> Product:
    return await service.update(db, user.user_id, product_id, body)


@router.post("/products/{product_id}/reviews", response_model=ReviewOut, status_code=201)
async def review(product_id: UUID, body: ReviewCreate, db: DbSession, user: Buyer) -> Review:
    return await service.review(db, user.user_id, product_id, body)


@router.get("/products/{product_id}/reviews", response_model=list[ReviewOut])
async def reviews(
    product_id: UUID, db: DbSession, limit: Limit = 20, offset: Offset = 0
) -> list[Review]:
    return list(
        (
            await db.scalars(
                select(Review)
                .where(Review.product_id == product_id)
                .order_by(Review.created_at.desc(), Review.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
