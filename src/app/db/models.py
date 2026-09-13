"""Explicit model registry used by Alembic and tests."""

from app.domains.catalog.models import Product, Review
from app.domains.events.models import AuditLog, OutboxEvent
from app.domains.finance.models import LedgerEntry, Payment, Settlement
from app.domains.identity.models import ActionToken, LoginSession, User
from app.domains.orders.models import Order, OrderItem, ReturnRequest
from app.domains.shopping.models import Address, CartItem

__all__ = [
    "ActionToken",
    "Address",
    "AuditLog",
    "CartItem",
    "LedgerEntry",
    "LoginSession",
    "Order",
    "OrderItem",
    "OutboxEvent",
    "Payment",
    "Product",
    "ReturnRequest",
    "Review",
    "Settlement",
    "User",
]
