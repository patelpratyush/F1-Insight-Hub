import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request

from f1_api.errors import ProblemError

log = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    """Client address for rate limiting.

    Behind N trusted proxies, the Nth address from the right of X-Forwarded-For was appended
    by our own proxy; everything left of it is client-controlled and must be ignored.
    """
    hops: int = getattr(request.app.state, "trusted_proxy_hops", 0)
    if getattr(request.app.state, "log_forwarded_headers", False):
        # shortcut: temporary diagnostics to learn what the platform proxy sends; remove after.
        log.info(
            "forwarded headers %s",
            {
                k: request.headers.get(k)
                for k in ("x-forwarded-for", "x-real-ip", "forwarded", "x-envoy-external-address")
            }
            | {"client": request.client.host if request.client else None},
        )
    forwarded = [
        h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()
    ]
    if hops > 0 and len(forwarded) >= hops:
        return forwarded[-hops]
    return request.client.host if request.client else "unknown"


def rate_limit(limit: int, window_seconds: int) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        client = client_ip(request)
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
