from fastapi import APIRouter, Depends

from app.api.deps import AuthUser, DbSession
from app.core.rate_limit import limit_auth
from app.domains.identity import service
from app.domains.identity.models import User
from app.domains.identity.schemas import (
    ActionResponse,
    EmailInput,
    Login,
    Register,
    ResetPassword,
    TokenInput,
    Tokens,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["Authentication"], dependencies=[Depends(limit_auth)])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: Register, db: DbSession) -> User:
    return await service.register(db, body)


@router.post("/login", response_model=Tokens)
async def login(body: Login, db: DbSession) -> Tokens:
    return await service.login(db, body)


@router.post("/refresh", response_model=Tokens)
async def refresh(body: TokenInput, db: DbSession) -> Tokens:
    return await service.refresh_session(db, body.token)


@router.post("/logout", status_code=204)
async def logout(db: DbSession, user: AuthUser) -> None:
    await service.logout(db, user.session_id)


@router.get("/me", response_model=UserOut)
async def me(db: DbSession, user: AuthUser) -> User | None:
    return await db.get(User, user.user_id)


@router.post("/verification/request", response_model=ActionResponse)
async def request_verification(body: EmailInput, db: DbSession) -> ActionResponse:
    return await service.request_action(db, str(body.email), "verify")


@router.post("/verification/confirm", status_code=204)
async def verify(body: TokenInput, db: DbSession) -> None:
    await service.consume_action(db, body.token, "verify")


@router.post("/password/request", response_model=ActionResponse)
async def request_reset(body: EmailInput, db: DbSession) -> ActionResponse:
    return await service.request_action(db, str(body.email), "reset")


@router.post("/password/reset", status_code=204)
async def reset(body: ResetPassword, db: DbSession) -> None:
    await service.consume_action(db, body.token, "reset", body.password)
