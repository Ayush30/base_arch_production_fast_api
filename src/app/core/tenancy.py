from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.messages import SecurityMsg

if TYPE_CHECKING:
    from uuid import UUID

# Holds the current tenant for the duration of a request
_current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)
_current_tenant_slug: ContextVar[str | None] = ContextVar("current_tenant_slug", default=None)


def set_current_tenant(tenant_id: UUID, tenant_slug: str) -> None:
    _current_tenant_id.set(tenant_id)
    _current_tenant_slug.set(tenant_slug)


def get_current_tenant_id() -> UUID:
    tid = _current_tenant_id.get()
    if tid is None:
        raise UnauthorizedError(SecurityMsg.TENANT_MISSING)
    return tid


def get_current_tenant_slug() -> str:
    slug = _current_tenant_slug.get()
    if slug is None:
        raise UnauthorizedError(SecurityMsg.TENANT_MISSING)
    return slug


def get_tenant_schema(slug: str) -> str:
    """Derive the PostgreSQL schema name from a validated tenant slug.

    The slug must already be validated via the registry — never accept
    raw user input here to prevent schema injection.
    """
    return f"{settings.tenant_schema_prefix}{slug}"


def current_schema() -> str:
    return get_tenant_schema(get_current_tenant_slug())
