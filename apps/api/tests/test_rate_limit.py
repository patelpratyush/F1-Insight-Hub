import logging

import pytest
from f1_api.errors import install_error_handlers
from f1_api.middleware.rate_limit import rate_limit
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis


def _app(redis: Redis) -> FastAPI:
    app = FastAPI()
    app.state.redis = redis
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
