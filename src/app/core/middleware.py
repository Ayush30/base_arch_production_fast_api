from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.metrics import record_http_request
from app.core.security import decode_token
from app.core.tenancy import set_current_tenant
from app.i18n import get_request_language, set_language

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import Request, Response
    from starlette.types import ASGIApp

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

PUBLIC_PATHS = {"/health", "/ready", "/docs", "/redoc", "/openapi.json", settings.metrics_path}


class LanguageMiddleware(BaseHTTPMiddleware):
    """Sets the active language ContextVar from the Accept-Language request header."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        lang = get_request_language(request.headers.get("Accept-Language", "en"))
        with set_language(lang):
            return await call_next(request)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class TenantMiddleware(BaseHTTPMiddleware):
    """Resolves tenant from the gateway-signed JWT and sets the tenant context var."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
                tenant_id: UUID = UUID(str(payload["tenant_id"]))
                tenant_slug: str = str(payload["tenant_slug"])
                set_current_tenant(tenant_id, tenant_slug)
                structlog.contextvars.bind_contextvars(
                    tenant_id=str(tenant_id),
                    user_id=str(payload.get("sub", "")),
                )
            except Exception:
                # Auth failures bubble up from the dependency layer with proper 401
                pass

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        route = str(getattr(request.scope.get("route"), "path", "unmatched"))

        if settings.metrics_enabled and request.url.path != settings.metrics_path:
            record_http_request(
                method=request.method,
                route=route,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        logger.info(
            "http_request",
            method=request.method,
            path=route,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response
