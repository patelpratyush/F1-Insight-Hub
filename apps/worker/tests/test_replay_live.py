import importlib.util
import json
from collections.abc import AsyncIterator
from pathlib import Path
from types import ModuleType

import pytest
from f1_core.live.codec import load_state
from redis.asyncio import Redis

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replay_live.py"
FIXTURE = Path(__file__).parent / "fixtures" / "live_replay_9999.jsonl"
KEY = 9999


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("replay_live", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
async def redis(redis_url: str) -> AsyncIterator[Redis]:
    r = Redis.from_url(redis_url)
    async for k in r.scan_iter(f"live:{KEY}*"):
        await r.delete(k)
    yield r
    await r.aclose()


async def _replay(redis: Redis, sleeps: list[float], speed: float = 5) -> int:
    async def fake_sleep(seconds: float) -> None:
        sleeps.append(round(seconds, 3))

    mod = _load()
    count: int = await mod.replay(redis, mod.read_fixture(FIXTURE), KEY, speed, sleep=fake_sleep)
    return count


async def test_replay_publishes_batches_in_scaled_time_with_unscaled_pause(redis: Redis) -> None:
    sleeps: list[float] = []
    published = await _replay(redis, sleeps)

    # fixture gaps (2, 3, 3, 2, 2 s) / speed 5, then the 25 s silence verbatim, then 3 s / 5
    assert sleeps == [0.4, 0.6, 0.6, 0.4, 0.4, 25.0, 0.6]
    entries = await redis.xrange(f"live:{KEY}")
    assert len(entries) == 8  # one stream entry per batch, like one per poll
    last_id, fields = entries[-1]
    assert last_id == f"{published}-0".encode()
    assert int(fields[b"seq"]) == published
    assert len(json.loads(fields[b"payload"])) == 3  # t=43 s: two intervals and the weather
    assert await redis.get(f"live:{KEY}:state") == fields[b"state"]


async def test_replay_final_state_reflects_overtake_pit_and_retirement(redis: Redis) -> None:
    await _replay(redis, [])
    raw = await redis.get(f"live:{KEY}:state")
    assert raw
    state = load_state(raw)
    tower = [d["number"] for d in json.loads(raw)["drivers"]]
    assert tower == [1, 16, 4, 44, 81]  # 16 passed 4; retired 81 sorted last
    assert state.status == "live" and state.lap == 3
    assert state.drivers[81].retired
    assert state.drivers[44].gap_to_leader == "+1 LAP" and state.drivers[44].interval is None
    assert state.drivers[44].in_pit is False  # pit-out lap after the pit-in
    assert state.drivers[44].compound == "HARD"
    assert state.drivers[1].sectors == ("purple", "purple", "purple")


async def test_replay_twice_starts_from_a_clean_stream(redis: Redis) -> None:
    first = await _replay(redis, [])
    second = await _replay(redis, [])
    assert second == first  # dedupe set and seq were reset, nothing dropped
    assert len(await redis.xrange(f"live:{KEY}")) == 8
