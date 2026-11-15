from httpx import AsyncClient
from redis.asyncio import Redis


async def test_healthz_is_ok(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_readyz_ok_when_dependencies_up(client: AsyncClient) -> None:
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["postgres"] == "ok"
    assert resp.json()["redis"] == "ok"


async def test_readyz_503_when_redis_down(client: AsyncClient) -> None:
    client._transport.app.state.redis = Redis.from_url(  # type: ignore[attr-defined]
        "redis://127.0.0.1:1/0", socket_connect_timeout=0.2
    )
    resp = await client.get("/readyz")
    assert resp.status_code == 503
    assert resp.json()["redis"] == "down"
    assert (await client.get("/healthz")).status_code == 200
