"""Idempotent local-only demo data. Never resets existing passwords or inventory."""

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import dispose_engines, marketplace_session
from app.domains.catalog.models import Product
from app.domains.identity.models import User
from app.domains.identity.repository import by_email
from app.domains.shopping.models import Address

DEMO_PASSWORDS = {
    role: f"{role.title()}-Demo-2026!"
    for role in ("buyer", "seller", "finance", "analytics", "admin")
}


async def seed() -> None:
    if not settings.is_local:
        raise RuntimeError("Demo seed is allowed only in APP_ENV=local")
    try:
        async with marketplace_session() as db:
            users = {}
            for role, password in DEMO_PASSWORDS.items():
                email = f"{role}@example.com"
                user = await by_email(db, email)
                if user is None:
                    user = User(
                        email=email,
                        name=f"Demo {role.title()}",
                        role=role,
                        password_hash=hash_password(password),
                        email_verified=True,
                        seller_approved=role == "seller",
                    )
                    db.add(user)
                    await db.flush()
                users[role] = user
            for sku, name, price in (
                ("BAG-001", "Everyday Backpack", 4999),
                ("MUG-001", "Travel Mug", 1999),
            ):
                existing = await db.scalar(
                    select(Product.id).where(
                        Product.seller_id == users["seller"].id, Product.sku == sku
                    )
                )
                if not existing:
                    db.add(
                        Product(
                            seller_id=users["seller"].id,
                            sku=sku,
                            name=name,
                            description="Demo physical product",
                            category="Lifestyle",
                            price_minor=price,
                            currency="USD",
                            stock=100,
                        )
                    )
            if not await db.scalar(select(Address.id).where(Address.buyer_id == users["buyer"].id)):
                db.add(
                    Address(
                        buyer_id=users["buyer"].id,
                        recipient="Demo Buyer",
                        line1="123 Example Street",
                        city="Example City",
                        region="CA",
                        postal_code="90001",
                        country_code="US",
                    )
                )
        print("Demo accounts and catalog ready. See README for local credentials.")
    finally:
        await dispose_engines()


if __name__ == "__main__":
    asyncio.run(seed())
