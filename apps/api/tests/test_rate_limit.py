import logging

import pytest
from f1_api.errors import install_error_handlers
from f1_api.middleware.rate_limit import rate_limit
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis


def _app(redis: Redis, trusted_proxy_hops: int = 0) -> FastAPI:
    app = FastAPI()
    app.state.redis = redis
    app.state.trusted_proxy_hops = trusted_proxy_hops
    install_error_handlers(app)

    @app.get("/limited", dependencies=[Depends(rate_limit(3, 60))])
    async def limited() -> dict[str, str]:
        return {"ok": "yes"}

    return app


async def test_blocks_after_limit(redis_url: str) -> None:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    async with AsyncClient(transport=ASGITransport(app=_app(redis)), base_url="http://t") as c:
        codes = [(await c.get("/limited")).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    await redis.aclose()


async def test_retry_after_header_present(redis_url: str) -> None:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    async with AsyncClient(transport=ASGITransport(app=_app(redis)), base_url="http://t") as c:
        for _ in range(3):
            await c.get("/limited")
        resp = await c.get("/limited")
    assert resp.status_code == 429
    assert int(resp.headers["retry-after"]) > 0
    await redis.aclose()


async def test_fails_open_when_redis_down(caplog: pytest.LogCaptureFixture) -> None:
    dead = Redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=0.2)
    with caplog.at_level(logging.WARNING, logger="f1_api.middleware.rate_limit"):
        async with AsyncClient(transport=ASGITransport(app=_app(dead)), base_url="http://t") as c:
            resp = await c.get("/limited")
    assert resp.status_code == 200
    assert any("failing open" in r.getMessage() for r in caplog.records)


async def test_spoofed_forwarded_for_cannot_evade_limit_behind_proxy(redis_url: str) -> None:
    """Behind one proxy, only the hop the proxy appended (rightmost) identifies the client."""
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    app = _app(redis, trusted_proxy_hops=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        codes = [
            (
                await c.get("/limited", headers={"X-Forwarded-For": f"10.0.0.{i}, 203.0.113.7"})
            ).status_code
            for i in range(5)
        ]
    assert codes == [200, 200, 200, 429, 429]
    await redis.aclose()


async def test_forwarded_for_ignored_without_trusted_proxy(redis_url: str) -> None:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    async with AsyncClient(transport=ASGITransport(app=_app(redis)), base_url="http://t") as c:
        codes = [
            (await c.get("/limited", headers={"X-Forwarded-For": f"10.0.0.{i}"})).status_code
            for i in range(5)
        ]
    assert codes == [200, 200, 200, 429, 429]
    await redis.aclose()


async def test_distinct_real_clients_get_separate_buckets(redis_url: str) -> None:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    app = _app(redis, trusted_proxy_hops=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        for _ in range(3):
            await c.get("/limited", headers={"X-Forwarded-For": "203.0.113.7"})
        other = await c.get("/limited", headers={"X-Forwarded-For": "198.51.100.9"})
    assert other.status_code == 200
    await redis.aclose()


async def test_forwarded_header_logging_is_opt_in(
    redis_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    headers = {"X-Forwarded-For": "198.51.100.1, 203.0.113.7", "X-Real-IP": "203.0.113.7"}
    with caplog.at_level(logging.INFO, logger="f1_api.middleware.rate_limit"):
        quiet = _app(redis)
        async with AsyncClient(transport=ASGITransport(app=quiet), base_url="http://t") as c:
            await c.get("/limited", headers=headers)
        assert not [r for r in caplog.records if "forwarded headers" in r.getMessage()]

        loud = _app(redis)
        loud.state.log_forwarded_headers = True
        async with AsyncClient(transport=ASGITransport(app=loud), base_url="http://t") as c:
            await c.get("/limited", headers=headers)
    msg = next(r.getMessage() for r in caplog.records if "forwarded headers" in r.getMessage())
    assert "198.51.100.1, 203.0.113.7" in msg and "x-real-ip" in msg
    await redis.aclose()
