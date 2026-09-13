"""Operational CLI: provision staff without a public privilege-escalation endpoint."""

import argparse
import asyncio
import getpass

from app.core.security import hash_password
from app.db.session import dispose_engines, marketplace_session
from app.domains.events.service import record_event
from app.domains.identity.models import User
from app.domains.identity.repository import by_email
from app.domains.identity.schemas import Register


async def create(email: str, name: str, role: str, password: str) -> None:
    validated = Register(email=email, name=name, password=password)
    try:
        async with marketplace_session() as db:
            if await by_email(db, str(validated.email)):
                raise ValueError("Email is already registered")
            user = User(
                email=str(validated.email).lower(),
                name=name,
                role=role,
                password_hash=hash_password(password),
                email_verified=True,
            )
            db.add(user)
            await db.flush()
            record_event(db, None, "staff.provisioned", user.id, role=role)
        print("Staff account created")
    finally:
        await dispose_engines()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", choices=["admin", "finance", "analytics"], required=True)
    args = parser.parse_args()
    password = getpass.getpass("Password (12+ characters): ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")
    asyncio.run(create(args.email, args.name, args.role, password))
