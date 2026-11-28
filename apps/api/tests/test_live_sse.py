import asyncio
import json
import socket
from collections.abc import AsyncIterator

import httpx
import pytest
import uvicorn
from f1_api.config import Settings
from f1_api.main import create_app
from f1_core.live.codec import dump_state
from f1_core.live.state import DriverTiming, TimingState
from redis.asyncio import Redis

KEY = 9999


def _state(seq: int) -> str:
    drivers = {1: DriverTiming(number=1, position=1), 4: DriverTiming(number=4, position=2)}
    return dump_state(TimingState(drivers=drivers, last_seq=seq, status="live"))


@pytest.fixture
async def redis(redis_url: str) -> AsyncIterator[Redis]:
    r = Redis.from_url(redis_url, decode_responses=True)
    for pattern in ("live:*",):
        async for k in r.scan_iter(pattern):
            await r.delete(k)
    yield r
    await r.aclose()


@pytest.fixture
async def seeded(redis: Redis) -> None:
    for seq in range(1, 6):
        await redis.xadd(
            f"live:{KEY}", {"seq": seq, "payload": "[]", "state": _state(seq)}, id=f"{seq}-0"
        )
    await redis.set(f"live:{KEY}:state", _state(5))


@pytest.fixture
async def base_url(settings: Settings, redis: Redis) -> AsyncIterator[str]:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    config = uvicorn.Config(
        create_app(settings),
        host="127.0.0.1",
        port=port,
        log_config=None,  # leave global logging alone for other tests
        timeout_graceful_shutdown=1,
    )
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    while not server.started:  # noqa: ASYNC110 - uvicorn exposes no started event
        await asyncio.sleep(0.02)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    await task


class Frames:
    """Incremental SSE parser over one response (comments become {"comment": ...})."""

    def __init__(self, resp: httpx.Response) -> None:
        self.lines = resp.aiter_lines()

    async def take(self, count: int) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        frame: dict[str, str] = {}
        async with asyncio.timeout(5):
            async for line in self.lines:
                if line.startswith(":"):
                    out.append({"comment": line[1:].strip()})
                elif line == "" and frame:
                    out.append(frame)
                    frame = {}
                elif line:
                    field, _, value = line.partition(":")
                    frame[field] = value.removeprefix(" ")
                if len(out) == count:
                    return out
        return out


async def _events(resp: httpx.Response, count: int) -> list[dict[str, str]]:
    return await Frames(resp).take(count)


async def test_stream_replays_after_last_event_id(base_url: str, seeded: None) -> None:
    async with (
        httpx.AsyncClient(base_url=base_url) as c,
        c.stream("GET", f"/v1/live/{KEY}/stream", headers={"Last-Event-ID": "3"}) as r,
    ):
        assert r.headers["content-type"].startswith("text/event-stream")
        frames = await _events(r, 2)
    assert [f["id"] for f in frames] == ["4", "5"]
    assert {f["event"] for f in frames} == {"tower"}
    assert json.loads(frames[1]["data"])["last_seq"] == 5


async def test_fresh_client_gets_snapshot_then_new_entries_without_duplicates(
    base_url: str, seeded: None, redis: Redis
) -> None:
    async with (
        httpx.AsyncClient(base_url=base_url) as c,
        c.stream("GET", f"/v1/live/{KEY}/stream") as r,
    ):
        frames = Frames(r)
        first = (await frames.take(1))[0]
        await redis.xadd(f"live:{KEY}", {"seq": 6, "payload": "[]", "state": _state(6)}, id="6-0")
        nxt = (await frames.take(1))[0]
    assert first["id"] == "5"
    assert nxt["id"] == "6"
    assert [d["number"] for d in json.loads(first["data"])["drivers"]] == [1, 4]


async def test_no_data_emits_waiting_then_heartbeats(
    base_url: str, redis: Redis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_api.routers.live.HEARTBEAT_SECONDS", 0.05)
    async with (
        httpx.AsyncClient(base_url=base_url) as c,
        c.stream("GET", "/v1/live/8888/stream") as r,
    ):
        frames = await _events(r, 2)
    assert json.loads(frames[0]["data"])["status"] == "waiting"
    assert "id" not in frames[0]
    assert frames[1] == {"comment": "heartbeat"}


async def test_per_ip_stream_limit_returns_429_and_releases(base_url: str, redis: Redis) -> None:
    async with httpx.AsyncClient(base_url=base_url) as c:
        streams, readers = [], []  # keep readers alive: a GC'd line iterator closes the stream
        for _ in range(3):
            cm = c.stream("GET", "/v1/live/1/stream")
            reader = Frames(await cm.__aenter__())
            await reader.take(1)
            streams.append(cm)
            readers.append(reader)
        over = await c.get("/v1/live/1/stream")
        assert over.status_code == 429
        assert over.headers["content-type"].startswith("application/problem+json")
        for cm in streams:
            await cm.__aexit__(None, None, None)
        async with asyncio.timeout(5):
            while int(await redis.get("live:conn:127.0.0.1") or 0) > 0:  # noqa: ASYNC110
                await asyncio.sleep(0.05)
        async with c.stream("GET", "/v1/live/1/stream") as again:
            assert again.status_code == 200


async def test_snapshot_returns_waiting_when_no_data(base_url: str, redis: Redis) -> None:
    async with httpx.AsyncClient(base_url=base_url) as c:
        r = await c.get("/v1/live/12345/snapshot")
    assert r.status_code == 200 and r.json()["status"] == "waiting"
    assert r.json()["drivers"] == []


async def test_snapshot_returns_ordered_tower(base_url: str, seeded: None) -> None:
    async with httpx.AsyncClient(base_url=base_url) as c:
        body = (await c.get(f"/v1/live/{KEY}/snapshot")).json()
    assert [d["number"] for d in body["drivers"]] == [1, 4] and body["last_seq"] == 5
