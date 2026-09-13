from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.messages import SecurityMsg
from app.core.security import decode_token
from app.db.session import get_db_session, get_read_db_session

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

_bearer = HTTPBearer()


class CurrentUser:
    def __init__(self, user_id: UUID, tenant_id: UUID, tenant_slug: str, roles: list[str]) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.tenant_slug = tenant_slug
        self.roles = roles

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> CurrentUser:
    payload = decode_token(credentials.credentials)
    try:
        return CurrentUser(
            user_id=UUID(str(payload["sub"])),
            tenant_id=UUID(str(payload["tenant_id"])),
            tenant_slug=str(payload["tenant_slug"]),
            roles=list(payload.get("roles", [])),
        )
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError(SecurityMsg.TOKEN_CLAIMS_MALFORMED) from exc


async def get_db(
    _: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncGenerator[AsyncSession, None]:
    """DB session scoped to the authenticated tenant."""
    async for session in get_db_session():
        yield session


async def get_read_db(
    _: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncGenerator[AsyncSession, None]:
    """Read-only DB session routed to replica when DATABASE_READ_REPLICA_URL is set."""
    async for session in get_read_db_session():
        yield session


# Convenience type aliases for route signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
ReadDbSession = Annotated[AsyncSession, Depends(get_read_db)]
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]
