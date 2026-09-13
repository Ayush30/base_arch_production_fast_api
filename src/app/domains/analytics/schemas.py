from uuid import UUID

from pydantic import BaseModel


class CurrencySales(BaseModel):
    currency: str
    paid_orders: int
    gross_minor: int
    commission_minor: int


class ProductSales(BaseModel):
    product_id: UUID
    currency: str
    units: int
    gross_minor: int


class SellerSales(BaseModel):
    seller_id: UUID
    currency: str
    units: int
    gross_minor: int
    commission_minor: int
