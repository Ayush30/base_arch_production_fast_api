from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Register(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    role: Literal["buyer", "seller"] = "buyer"


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenInput(BaseModel):
    token: str = Field(min_length=20, max_length=512)


class EmailInput(BaseModel):
    email: EmailStr


class ResetPassword(TokenInput):
    password: str = Field(min_length=12, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    name: str
    role: str
    is_active: bool
    email_verified: bool
    seller_approved: bool
    created_at: datetime


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ActionResponse(BaseModel):
    message: str = "If the account is eligible, a token has been issued."
    development_token: str | None = None
