from __future__ import annotations

import hashlib
import pathlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except (VerificationError, InvalidHashError):
        return False


def opaque_token() -> str:
    return secrets.token_urlsafe(48)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def access_token(user_id: str, session_id: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": user_id,
            "sid": session_id,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        pathlib.Path(settings.jwt_private_key_path).read_text(),
        algorithm="RS256",
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            pathlib.Path(settings.jwt_public_key_path).read_text(),
            algorithms=["RS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={
                "require_exp": True,
                "require_iat": True,
                "require_sub": True,
                "require_aud": True,
                "require_iss": True,
            },
        )
        if payload.get("type") != "access" or not isinstance(payload.get("sid"), str):
            raise JWTError("Invalid token type/session")
        return payload
    except (JWTError, ValueError, TypeError) as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc
