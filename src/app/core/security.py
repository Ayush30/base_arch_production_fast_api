from __future__ import annotations

import pathlib
from typing import Any

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.messages import SecurityMsg

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _load_key(path: str) -> str:
    return pathlib.Path(path).read_text()


def decode_token(token: str) -> dict[str, Any]:
    try:
        public_key = _load_key(settings.jwt_public_key_path)
        payload: dict[str, Any] = jwt.decode(
            token,
            public_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        logger.warning("jwt_decode_failed", error=str(exc))
        raise UnauthorizedError(SecurityMsg.TOKEN_INVALID) from exc


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return bool(_pwd_context.verify(plain, hashed))
