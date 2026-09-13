from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import configure_logging
from app.core.middleware import (
    CorrelationIdMiddleware,
    LanguageMiddleware,
    RequestLoggingMiddleware,
)
from app.core.telemetry import configure_telemetry, mount_metrics
from app.db.session import dispose_engines
from app.kafka.producer import stop_kafka_producer

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", service=settings.app_name, env=settings.app_env)
    yield
    await stop_kafka_producer()
    await dispose_engines()
    logger.info("shutdown")


def create_app() -> FastAPI:
    configure_logging()
    configure_telemetry()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.app_docs_enabled else None,
        redoc_url="/redoc" if settings.app_docs_enabled else None,
        lifespan=lifespan,
    )

    # Middleware — outermost first (executed inside-out)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(LanguageMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-ID"],
        expose_headers=["X-Correlation-ID"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": "Record conflicts with existing data or a database constraint",
                    "details": [],
                }
            },
        )

    # Exception handlers
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    # Routers
    from app.api.v1.router import v1_router

    app.include_router(v1_router)
    mount_metrics(app)

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_local,
        timeout_keep_alive=60,
        timeout_graceful_shutdown=60,
    )


if __name__ == "__main__":
    run()
