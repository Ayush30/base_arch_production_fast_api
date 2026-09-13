from __future__ import annotations

import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app.core.messages import HealthMsg
from app.db.session import engine
from app.i18n import t

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe", operation_id="health_live")
async def liveness() -> dict[str, str]:
    return {"status": t(HealthMsg.OK)}


@router.get("/ready", summary="Readiness probe", operation_id="health_ready")
async def readiness() -> dict[str, str]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("readiness_db_check_failed", error=str(exc))
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=503,
            content={
                "status": t(HealthMsg.UNAVAILABLE),
                "detail": t(HealthMsg.DETAIL_DB),
            },
        )
    return {"status": t(HealthMsg.OK)}
