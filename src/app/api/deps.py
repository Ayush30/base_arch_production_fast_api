from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable  # noqa: TC003
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import marketplace_session
from app.domains.identity.models import LoginSession, User

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with marketplace_session() as db:
        yield db


DbSession = Annotated[AsyncSession, Depends(get_db)]
# Primary reads ensure current permissions and read-after-write consistency.
ReadDbSession = DbSession


class CurrentUser:
    def __init__(self, user: User, session_id: UUID) -> None:
        self.user_id = user.id
        self.role = user.role
        self.roles = [user.role]
        self.session_id = session_id
        self.seller_approved = user.seller_approved
        self.email_verified = user.email_verified

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    if credentials is None:
        raise UnauthorizedError("Bearer token required")
    payload = decode_token(credentials.credentials)
    try:
        user_id, session_id = UUID(payload["sub"]), UUID(payload["sid"])
    except (KeyError, ValueError, TypeError) as exc:
        raise UnauthorizedError("Malformed access token") from exc
    # Reload permissions on every request; disabling a user/revoking a session is immediate.
    user = await db.get(User, user_id)
    session = await db.scalar(
        select(LoginSession).where(
            LoginSession.id == session_id,
            LoginSession.user_id == user_id,
            LoginSession.revoked.is_(False),
            LoginSession.expires_at > datetime.now(UTC),
        )
    )
    if user is None or not user.is_active or session is None:
        raise UnauthorizedError("Session is no longer active")
    return CurrentUser(user, session_id)


AuthUser = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: str) -> Callable[..., Awaitable[CurrentUser]]:
    async def check(user: AuthUser) -> CurrentUser:
        if user.role not in roles:
            raise ForbiddenError("Your role cannot perform this action")
        if user.role == "seller" and not user.seller_approved:
            raise ForbiddenError("Seller approval required")
        return user

    return check


Buyer = Annotated[CurrentUser, Depends(require_roles("buyer"))]
Seller = Annotated[CurrentUser, Depends(require_roles("seller"))]
Finance = Annotated[CurrentUser, Depends(require_roles("finance", "admin"))]
Analyst = Annotated[CurrentUser, Depends(require_roles("analytics", "admin"))]
Admin = Annotated[CurrentUser, Depends(require_roles("admin"))]
