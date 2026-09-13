from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    recipient: str = Field(min_length=1, max_length=100)
    line1: str = Field(min_length=1, max_length=200)
    line2: str = Field(default="", max_length=200)
    city: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country_code: str = Field(pattern="^[A-Z]{2}$")


class AddressOut(AddressCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class CartPut(BaseModel):
    quantity: int = Field(ge=1, le=100, strict=True)


class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: UUID
    quantity: int
