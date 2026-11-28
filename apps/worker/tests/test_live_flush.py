import uuid
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from typing import Any

import pytest
from f1_db.models import Driver, LapRecord, PitStop, Race, RaceSession, Season, Stint
from f1_worker.jobs.live_flush import flush_live_session
from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

KEY = 4242

RECORDS: dict[str, list[dict[str, Any]]] = {
    "laps": [
        {
            "driver_number": 1,
            "lap_number": 1,
            "lap_duration": 95.5,
            "duration_sector_1": None,
            "duration_sector_2": 30.2,
            "duration_sector_3": 31.1,
            "is_pit_out_lap": True,
        },
        {
            "driver_number": 1,
            "lap_number": 2,
            "lap_duration": 90.0,
            "duration_sector_1": 29.0,
            "duration_sector_2": 30.0,
            "duration_sector_3": 31.0,
            "is_pit_out_lap": False,
        },
        {"driver_number": 99, "lap_number": 1, "lap_duration": 99.0},  # unknown driver: skipped
    ],
    "pit": [{"driver_number": 1, "lap_number": 20, "pit_duration": 22.4}],
    "stints": [
        {
            "driver_number": 1,
            "stint_number": 1,
            "compound": "MEDIUM",
            "lap_start": 1,
            "lap_end": 20,
        },
        {
            "driver_number": 1,
            "stint_number": 2,
            "compound": "HARD",
            "lap_start": 21,
            "lap_end": None,
        },
    ],
}


class FakeOpenF1:
    async def records(self, endpoint: str, session_key: int) -> list[dict[str, Any]]:
        assert session_key == KEY
        return RECORDS[endpoint]


@pytest.fixture
async def redis(redis_url: str) -> AsyncIterator[Redis]:
    r = Redis.from_url(redis_url)
    await r.flushdb()
    yield r
    await r.aclose()


@pytest.fixture
async def session_id(session_factory: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    async with session_factory() as s:
        await s.execute(text("truncate seasons, drivers cascade"))
        season = Season(year=1995)
        driver = Driver(ref="max", code="VER", given_name="Max", family_name="V", number=1)
        s.add_all([season, driver])
        await s.flush()
        race = Race(
            season_id=season.id, round=1, name="GP", circuit_name="C", race_date=date(1995, 3, 5)
        )
        s.add(race)
        await s.flush()
        rs = RaceSession(
            race_id=race.id,
            type="R",
            status="finished",
            openf1_session_key=KEY,
            starts_at=datetime(1995, 3, 5, 14, tzinfo=UTC),
        )
        s.add(rs)
        await s.commit()
        return rs.id


async def _counts(sf: async_sessionmaker[AsyncSession]) -> list[int]:
    async with sf() as s:
        return [
            (await s.execute(select(func.count()).select_from(m))).scalar_one()
            for m in (LapRecord, PitStop, Stint)
        ]


async def test_flush_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession], session_id: uuid.UUID, redis: Redis
) -> None:
    await redis.set(f"live:{KEY}:state", "{}")
    ctx = {"session_factory": session_factory, "openf1": FakeOpenF1(), "redis": redis}
    assert await flush_live_session(ctx, session_id) == 5
    assert await flush_live_session(ctx, session_id) == 5
    assert await _counts(session_factory) == [2, 1, 2]
    assert 0 < await redis.ttl(f"live:{KEY}:state") <= 6 * 3600
    async with session_factory() as s:
        hard = (await s.execute(select(Stint).where(Stint.stint_number == 2))).scalar_one()
        pit = (await s.execute(select(PitStop))).scalar_one()
    assert (hard.compound, hard.lap_end) == ("HARD", None)
    assert pit.duration_ms == 22400


async def test_flush_handles_missing_sector_times_as_none(
    session_factory: async_sessionmaker[AsyncSession], session_id: uuid.UUID, redis: Redis
) -> None:
    ctx = {"session_factory": session_factory, "openf1": FakeOpenF1(), "redis": redis}
    await flush_live_session(ctx, session_id)
    async with session_factory() as s:
        lap1 = (await s.execute(select(LapRecord).where(LapRecord.lap_number == 1))).scalar_one()
    assert (lap1.s1_ms, lap1.s2_ms, lap1.lap_time_ms, lap1.is_pit_out) == (None, 30200, 95500, True)


async def test_flush_without_session_key_is_noop(
    session_factory: async_sessionmaker[AsyncSession], redis: Redis
) -> None:

    ctx = {"session_factory": session_factory, "openf1": FakeOpenF1(), "redis": redis}
    assert await flush_live_session(ctx, uuid.uuid4()) == 0
