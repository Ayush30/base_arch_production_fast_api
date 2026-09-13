from fastapi import APIRouter

from app.api.deps import Analyst, DbSession, Seller
from app.domains.analytics import repository
from app.domains.analytics.schemas import CurrencySales, ProductSales, SellerSales
from app.domains.catalog.router import Limit, Offset

router = APIRouter(tags=["Analytics"])


@router.get("/analytics/sales", response_model=list[CurrencySales])
async def sales(db: DbSession, user: Analyst) -> list[CurrencySales]:
    return await repository.sales(db)


@router.get("/analytics/products", response_model=list[ProductSales])
async def products(
    db: DbSession, user: Analyst, limit: Limit = 20, offset: Offset = 0
) -> list[ProductSales]:
    return await repository.product_sales(db, limit, offset)


@router.get("/analytics/sellers", response_model=list[SellerSales])
async def sellers(
    db: DbSession, user: Analyst, limit: Limit = 20, offset: Offset = 0
) -> list[SellerSales]:
    return await repository.seller_sales(db, limit, offset)


@router.get("/seller/sales", response_model=list[CurrencySales])
async def seller_sales(db: DbSession, user: Seller) -> list[CurrencySales]:
    return await repository.sales(db, user.user_id)
