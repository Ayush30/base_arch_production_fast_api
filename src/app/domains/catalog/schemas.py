from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    category: str = Field(min_length=1, max_length=80)
    image_url: HttpUrl | None = None
    price_minor: int = Field(gt=0, le=100_000_000, strict=True)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    stock: int = Field(default=0, ge=0, le=1_000_000, strict=True)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    price_minor: int | None = Field(default=None, gt=0, le=100_000_000, strict=True)
    stock: int | None = Field(default=None, ge=0, le=1_000_000, strict=True)
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    seller_id: UUID
    sku: str
    name: str
    description: str
    category: str
    image_url: str | None
    price_minor: int
    currency: str
    stock: int
    is_active: bool
    is_blocked: bool
    version: int
    created_at: datetime


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=2000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    rating: int
    comment: str
    created_at: datetime
