from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import configure_logging
from app.core.middleware import (
    CorrelationIdMiddleware,
    LanguageMiddleware,
    RequestLoggingMiddleware,
    TenantMiddleware,
)
from app.core.telemetry import configure_telemetry, mount_metrics
from app.db.session import dispose_engines
from app.kafka.producer import start_kafka_producer, stop_kafka_producer

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", service=settings.app_name, env=settings.app_env)
    await start_kafka_producer()
    logger.info("kafka_producer_started", bootstrap_servers=settings.kafka_bootstrap_servers)
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
    app.add_middleware(TenantMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(LanguageMiddleware)

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
