from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    access_token,
    hash_password,
    opaque_token,
    token_digest,
    verify_password,
)
from app.domains.events.service import record_event
from app.domains.identity.models import ActionToken, LoginSession, User
from app.domains.identity.repository import by_email
from app.domains.identity.schemas import ActionResponse, Login, Register, Tokens

# Equal-cost verification for nonexistent users reduces account enumeration by timing.
_dummy_hash = hash_password("not-a-real-user-password")


async def register(db: AsyncSession, body: Register) -> User:
    if await by_email(db, str(body.email)):
        raise ConflictError("Email is already registered")
    user = User(
        email=str(body.email).lower(),
        name=body.name,
        role=body.role,
        password_hash=await run_in_threadpool(hash_password, body.password),
    )
    db.add(user)
    await db.flush()
    record_event(db, user.id, "user.registered", user.id)
    await db.commit()
    return user


async def issue_session(db: AsyncSession, user: User) -> Tokens:
    refresh = opaque_token()
    session = LoginSession(
        user_id=user.id,
        refresh_hash=token_digest(refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    await db.flush()
    result = Tokens(
        access_token=access_token(str(user.id), str(session.id)),
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
    await db.commit()
    return result


async def login(db: AsyncSession, body: Login) -> Tokens:
    user = await by_email(db, str(body.email))
    valid = await run_in_threadpool(
        verify_password, body.password, user.password_hash if user else _dummy_hash
    )
    if not user or not valid or not user.is_active:
        raise UnauthorizedError("Invalid email or password")
    return await issue_session(db, user)


async def refresh_session(db: AsyncSession, token: str) -> Tokens:
    session = await db.scalar(
        select(LoginSession)
        .where(LoginSession.refresh_hash == token_digest(token))
        .with_for_update()
    )
    if not session or session.revoked or session.expires_at <= datetime.now(UTC):
        raise UnauthorizedError("Invalid or expired refresh token")
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Account is disabled")
    # Rotation creates a new session and invalidates the old access token too.
    session.revoked = True
    return await issue_session(db, user)


async def request_action(db: AsyncSession, email: str, purpose: str) -> ActionResponse:
    if not settings.local_email_tokens_enabled or not settings.is_local:
        error = ValidationError("Email delivery adapter is not configured")
        error.status_code = 503
        raise error
    user = await by_email(db, email)
    response = ActionResponse()
    if user and user.is_active:
        token = opaque_token()
        db.add(
            ActionToken(
                user_id=user.id,
                purpose=purpose,
                token_hash=token_digest(token),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        response.development_token = token
        await db.commit()
    return response


async def consume_action(
    db: AsyncSession, token: str, purpose: str, password: str | None = None
) -> None:
    action = await db.scalar(
        select(ActionToken)
        .where(
            ActionToken.token_hash == token_digest(token),
            ActionToken.purpose == purpose,
            ActionToken.used.is_(False),
        )
        .with_for_update()
    )
    if not action or action.expires_at <= datetime.now(UTC):
        raise ValidationError("Invalid or expired action token")
    user = await db.scalar(select(User).where(User.id == action.user_id).with_for_update())
    if not user or not user.is_active:
        raise ValidationError("Account is unavailable")
    action.used = True
    if purpose == "verify":
        user.email_verified = True
    else:
        if password is None:
            raise ValidationError("Password is required")
        user.password_hash = await run_in_threadpool(hash_password, password)
        await db.execute(
            update(LoginSession).where(LoginSession.user_id == user.id).values(revoked=True)
        )
        await db.execute(
            update(ActionToken)
            .where(ActionToken.user_id == user.id, ActionToken.purpose == "reset")
            .values(used=True)
        )
    record_event(db, user.id, f"user.{purpose}", user.id)
    await db.commit()


async def logout(db: AsyncSession, session_id: UUID) -> None:
    await db.execute(update(LoginSession).where(LoginSession.id == session_id).values(revoked=True))
    await db.commit()
