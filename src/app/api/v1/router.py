from fastapi import APIRouter

from app.api.v1.routes.health import router as health
from app.domains.administration.router import router as administration
from app.domains.analytics.router import router as analytics
from app.domains.catalog.router import router as catalog
from app.domains.finance.router import router as finance
from app.domains.identity.router import router as identity
from app.domains.orders.router import router as orders
from app.domains.shopping.router import router as shopping

v1_router = APIRouter(prefix="/api/v1")
for router in (health, identity, catalog, shopping, orders, finance, analytics, administration):
    v1_router.include_router(router)
