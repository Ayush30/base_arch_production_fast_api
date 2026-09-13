from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.domains.administration.schemas import UserUpdate
from app.domains.events.service import record_event
from app.domains.identity.models import LoginSession, User


async def update_user(db: AsyncSession, actor_id: UUID, user_id: UUID, body: UserUpdate) -> User:
    user = await db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise NotFoundError("User not found")
    if user.role == "admin" and body.is_active is False:
        raise ValidationError("Disable administrators through an audited operational procedure")
    if body.seller_approved is not None:
        if user.role != "seller":
            raise ValidationError("Only sellers can receive seller approval")
        user.seller_approved = body.seller_approved
    if body.is_active is not None:
        user.is_active = body.is_active
        if not body.is_active:
            await db.execute(
                update(LoginSession).where(LoginSession.user_id == user.id).values(revoked=True)
            )
    record_event(db, actor_id, "user.admin_updated", user.id, **body.model_dump(exclude_none=True))
    await db.commit()
    return user
