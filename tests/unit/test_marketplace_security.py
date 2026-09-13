from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from jose import jwt
from pydantic import ValidationError
from redis.exceptions import ConnectionError
from starlette.requests import Request

from app.core.config import Settings, settings
from app.core.exceptions import AppError, NotFoundError, RateLimitError, UnauthorizedError
from app.core.money import commission
from app.core.rate_limit import limit_auth
from app.core.security import access_token, decode_token, hash_password, verify_password
from app.domains.finance.service import require_local_payments


@pytest.mark.parametrize(
    ("amount", "bps", "expected"), [(1999, 1000, 200), (5, 1000, 1), (100, 0, 0), (100, 10000, 100)]
)
def test_commission_rounds_minor_units(amount: int, bps: int, expected: int) -> None:
    assert commission(amount, bps) == expected


def test_password_and_token_security() -> None:
    hashed = hash_password("Secure-password-2026!")
    assert verify_password("Secure-password-2026!", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("wrong", "malformed")
    assert decode_token(access_token(str(uuid4()), str(uuid4())))["type"] == "access"
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid4()),
        "sid": str(uuid4()),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=1),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    for changes in (
        {"aud": "another-app"},
        {"iss": "attacker"},
        {"exp": now - timedelta(minutes=1)},
        {"type": "refresh"},
        {"sid": None},
    ):
        encoded = jwt.encode(
            {**payload, **changes},
            Path(settings.jwt_private_key_path).read_text(),
            algorithm="RS256",
        )
        with pytest.raises(UnauthorizedError):
            decode_token(encoded)


@pytest.mark.parametrize(
    "overrides",
    [
        {"local_payments_enabled": True},
        {"local_email_tokens_enabled": True},
        {"debug": True},
        {"rate_limit_enabled": False},
        {"allowed_hosts": ["*"]},
    ],
)
def test_production_rejects_unsafe_config(overrides: dict) -> None:
    baseline = {
        "app_env": "production",
        "local_payments_enabled": False,
        "local_email_tokens_enabled": False,
        "APP_DEBUG": False,
    }
    if "debug" in overrides:
        overrides = {"APP_DEBUG": overrides["debug"]}
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(baseline | overrides))


def test_simulation_unavailable_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(NotFoundError):
        require_local_payments()


async def test_rate_limiter_and_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    request = Request({"type": "http", "client": ("127.0.0.1", 1234), "headers": []})
    redis = AsyncMock()
    redis.__aenter__.return_value = redis
    with patch("app.core.rate_limit.Redis.from_url", return_value=redis):
        redis.eval.return_value = 1
        await limit_auth(request)
        redis.eval.return_value = settings.auth_rate_limit + 1
        with pytest.raises(RateLimitError):
            await limit_auth(request)
        redis.eval.side_effect = ConnectionError("redis unavailable")
        with pytest.raises(AppError) as error:
            await limit_auth(request)
        assert error.value.status_code == 503


def test_missing_audience_rejected() -> None:
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid4()),
        "sid": str(uuid4()),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=1),
        "iss": settings.jwt_issuer,
    }
    token = jwt.encode(payload, Path(settings.jwt_private_key_path).read_text(), algorithm="RS256")
    with pytest.raises(UnauthorizedError):
        decode_token(token)
