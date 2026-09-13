from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.domains.example.router import router as example_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(health_router)
v1_router.include_router(example_router)
