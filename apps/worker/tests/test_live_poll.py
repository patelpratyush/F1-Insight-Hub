import json
from collections.abc import AsyncIterator, Mapping
from datetime import UTC, date, datetime

import pytest
from f1_core.live.codec import load_state
from f1_core.live.events import LiveEvent
from f1_db.models import Race, RaceSession, Season
from f1_worker.jobs.live_poll import poll_live_session, poll_once
from f1_worker.sources.openf1 import OpenF1Unavailable
from redis.asyncio import Redis
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

KEY = 7777
T = datetime(2025, 3, 16, 4, 0, tzinfo=UTC)


def ev(sec: int, kind: str, number: int | None, **data: object) -> LiveEvent:
    return LiveEvent(seq=0, ts=T.replace(second=sec), kind=kind, driver_number=number, data=data)  # type: ignore[arg-type]


class FakeClient:
    def __init__(self, *batches: list[LiveEvent] | Exception) -> None:
        self.batches = list(batches)
        self.afters: list[dict[str, datetime]] = []

    async def events_since(
        self, session_key: int, after: Mapping[str, datetime] | None
    ) -> list[LiveEvent]:
        self.afters.append(dict(after or {}))
        batch = self.batches.pop(0) if self.batches else []
        if isinstance(batch, Exception):
            raise batch
        return batch


@pytest.fixture
async def redis(redis_url: str) -> AsyncIterator[Redis]:
    r = Redis.from_url(redis_url)  # bytes responses, like arq's ctx["redis"]
    await r.flushdb()
    yield r
    await r.aclose()


async def _payload_seqs(redis: Redis) -> list[int]:
    entries = await redis.xrange(f"live:{KEY}")
    return [e["seq"] for _, f in entries for e in json.loads(f[b"payload"])]


async def test_poller_publishes_ordered_seq_and_state(redis: Redis) -> None:
    client = FakeClient(
        [ev(1, "position", 4, position=2), ev(2, "position", 1, position=1)],
        [ev(3, "interval", 4, gap_to_leader="+1 LAP", interval=None)],
    )
    assert await poll_once(redis, client, KEY) == 3  # status:live + 2 events
    assert await poll_once(redis, client, KEY) == 1
    assert await _payload_seqs(redis) == [1, 2, 3, 4]
    ids = [i for i, _ in await redis.xrange(f"live:{KEY}")]
    assert ids == [b"3-0", b"4-0"]  # stream id == last seq in the entry
    state = load_state(await redis.get(f"live:{KEY}:state") or b"")
    assert state.status == "live" and state.last_seq == 4
    assert state.drivers[1].position == 1 and state.drivers[4].gap_to_leader == "+1 LAP"
    assert client.afters[1] == {"position": T.replace(second=2)}


async def test_poller_does_not_duplicate_events_across_polls(redis: Redis) -> None:
    same = [ev(1, "position", 1, position=1)]
    client = FakeClient(same, list(same), [])
    assert await poll_once(redis, client, KEY) == 2
    assert await poll_once(redis, client, KEY) == 0
    assert await poll_once(redis, client, KEY) == 0
    assert await redis.xlen(f"live:{KEY}") == 1


async def test_poller_publishes_waiting_status_on_upstream_error(redis: Redis) -> None:
    client = FakeClient(
        OpenF1Unavailable("down"),
        [ev(1, "position", 1, position=1)],
        OpenF1Unavailable("down"),
        OpenF1Unavailable("still down"),
    )
    assert await poll_once(redis, client, KEY) == 0  # already waiting: nothing to publish
    assert await poll_once(redis, client, KEY) == 2
    assert await poll_once(redis, client, KEY) == 1
    assert await poll_once(redis, client, KEY) == 0
    state = load_state(await redis.get(f"live:{KEY}:state") or b"")
    assert state.status == "waiting" and state.drivers[1].position == 1


async def test_empty_poll_keeps_live_status(redis: Redis) -> None:
    client = FakeClient([ev(1, "position", 1, position=1)], [])
    await poll_once(redis, client, KEY)
    assert await poll_once(redis, client, KEY) == 0
    state = load_state(await redis.get(f"live:{KEY}:state") or b"")
    assert state.status == "live"


async def test_keys_expire(redis: Redis) -> None:
    await poll_once(redis, FakeClient([ev(1, "position", 1, position=1)]), KEY)
    for suffix in ("", ":state", ":seq", ":seen", ":cursor"):
        assert 0 < await redis.ttl(f"live:{KEY}{suffix}") <= 24 * 3600


async def test_loop_runs_while_session_is_live(
    redis: Redis, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as s:
        await s.execute(text("truncate seasons cascade"))
        season = Season(year=1996)
        s.add(season)
        await s.flush()
        race = Race(
            season_id=season.id, round=1, name="GP", circuit_name="C", race_date=date(1996, 3, 10)
        )
        s.add(race)
        await s.flush()
        s.add(
            RaceSession(
                race_id=race.id, type="R", starts_at=T, status="live", openf1_session_key=KEY
            )
        )
        await s.commit()

    class FinishingClient(FakeClient):
        async def events_since(
            self, session_key: int, after: Mapping[str, datetime] | None
        ) -> list[LiveEvent]:
            async with session_factory() as s:
                await s.execute(
                    update(RaceSession)
                    .where(RaceSession.openf1_session_key == KEY)
                    .values(status="finished")
                )
                await s.commit()
            return [ev(1, "position", 1, position=1)]

    ctx = {
        "redis": redis,
        "session_factory": session_factory,
        "openf1": FinishingClient(),
        "openf1_poll_seconds": 0.0,
    }
    assert await poll_live_session(ctx, KEY) == 2
