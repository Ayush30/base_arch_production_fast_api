"""Shared Redis counter: limits work across API replicas, without trusting proxy headers."""

import hashlib

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.exceptions import AppError, RateLimitError

_script = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return count
"""


async def limit_auth(request: Request) -> None:
    if not settings.rate_limit_enabled:
        return
    host = request.client.host if request.client else "unknown"
    key = "auth:" + hashlib.sha256(host.encode()).hexdigest()
    try:
        async with Redis.from_url(settings.redis_url) as redis:
            count = await redis.eval(_script, 1, key, 60)
    except RedisError as exc:
        error = AppError("Authentication temporarily unavailable")
        error.status_code = 503
        raise error from exc
    if int(count) > settings.auth_rate_limit:
        raise RateLimitError("Too many authentication attempts; retry in one minute")
