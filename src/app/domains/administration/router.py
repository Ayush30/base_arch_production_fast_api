from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import Admin, DbSession
from app.domains.administration import service
from app.domains.administration.schemas import AuditOut, ModerateProduct, UserUpdate
from app.domains.catalog.models import Product
from app.domains.catalog.repository import get_product
from app.domains.catalog.router import Limit, Offset
from app.domains.catalog.schemas import ProductOut
from app.domains.events.models import AuditLog
from app.domains.events.service import record_event
from app.domains.identity.models import User
from app.domains.identity.schemas import UserOut

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/users", response_model=list[UserOut])
async def users(db: DbSession, user: Admin, limit: Limit = 20, offset: Offset = 0) -> list[User]:
    return list(
        (
            await db.scalars(
                select(User).order_by(User.created_at.desc(), User.id).limit(limit).offset(offset)
            )
        ).all()
    )


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: UUID, body: UserUpdate, db: DbSession, user: Admin) -> User:
    return await service.update_user(db, user.user_id, user_id, body)


@router.post("/products/{product_id}/moderation", response_model=ProductOut)
async def moderate(product_id: UUID, body: ModerateProduct, db: DbSession, user: Admin) -> Product:
    product = await get_product(db, product_id, lock=True)
    product.is_blocked = body.blocked
    product.version += 1
    record_event(db, user.user_id, "product.moderated", product.id, **body.model_dump())
    await db.commit()
    return product


@router.get("/audit", response_model=list[AuditOut])
async def audit(
    db: DbSession, user: Admin, limit: Limit = 20, offset: Offset = 0
) -> list[AuditLog]:
    return list(
        (
            await db.scalars(
                select(AuditLog)
                .order_by(AuditLog.created_at.desc(), AuditLog.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
