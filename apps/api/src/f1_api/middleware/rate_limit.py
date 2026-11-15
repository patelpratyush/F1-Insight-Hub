import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request

from f1_api.errors import ProblemError

log = logging.getLogger(__name__)


def rate_limit(limit: int, window_seconds: int) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        bucket = int(time.time()) // window_seconds
        key = f"rl:{request.url.path}:{client}:{bucket}"
        try:
            redis = request.app.state.redis
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window_seconds)
        except Exception:
            log.warning("rate limiter unavailable, failing open")
            return
        if count > limit:
            retry_after = window_seconds - (int(time.time()) % window_seconds)
            err = ProblemError(429, "Too many requests", f"Retry in {retry_after}s")
            err.headers = {"Retry-After": str(retry_after)}
            raise err

    return dependency
