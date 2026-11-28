import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from f1_db.models import Race, RaceSession, Season
from f1_worker.scheduling import decide_poll_interval, session_status, tick_sessions
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

NOW = datetime(2025, 3, 16, 4, 0, tzinfo=UTC)


def rs(offset_min: int, status: str = "scheduled", ends_at: datetime | None = None) -> RaceSession:
    return RaceSession(
        type="R", starts_at=NOW - timedelta(minutes=offset_min), status=status, ends_at=ends_at
    )


@pytest.mark.parametrize(
    ("offset_min", "live", "expected"),
    [
        (-10, False, 60),  # 10 min before start
        (-30, False, 60),  # exactly 30 min before
        (-40, False, 1800),  # 40 min before start
        (5, True, 2),  # live
        (500, False, 1800),  # long after
    ],
)
def test_decide_poll_interval(offset_min: int, live: bool, expected: int) -> None:
    s = rs(offset_min, "live" if live else "scheduled")
    assert decide_poll_interval(NOW, [s, rs(-5000)]) == expected


def test_decide_poll_interval_with_no_sessions() -> None:
    assert decide_poll_interval(NOW, []) == 1800


@pytest.mark.parametrize(
    ("offset_min", "status", "expected"),
    [
        (-10, "scheduled", "scheduled"),
        (-5, "scheduled", "live"),  # live from starts_at - 5 min
        (60, "scheduled", "live"),
        (180, "live", "finished"),  # starts_at + 3 h
        (60, "finished", "finished"),  # never reverts
    ],
)
def test_session_status_transitions(offset_min: int, status: str, expected: str) -> None:
    assert session_status(NOW, rs(offset_min, status)) == expected


def test_openf1_end_signal_finishes_early() -> None:
    assert session_status(NOW, rs(90, "live", ends_at=NOW - timedelta(minutes=1))) == "finished"


def test_cancelled_session_never_goes_live() -> None:
    for offset in (-5, 0, 60, 500):
        assert session_status(NOW, rs(offset, "cancelled")) == "cancelled"


class FakeArq:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    async def enqueue_job(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.jobs.append((name, args, kwargs))


class FakeOpenF1:
    def __init__(self, sessions: list[dict[str, Any]]) -> None:
        self.rows = sessions
        self.calls = 0

    async def sessions(self, year: int) -> list[dict[str, Any]]:
        self.calls += 1
        return self.rows


@pytest.fixture
async def race_id(session_factory: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    async with session_factory() as s:
        await s.execute(text("truncate seasons cascade"))
        season = Season(year=2025)
        s.add(season)
        await s.flush()
        race = Race(
            season_id=season.id,
            round=1,
            name="Australian GP",
            circuit_name="Albert Park",
            race_date=date(2025, 3, 16),
        )
        s.add(race)
        await s.flush()
        s.add_all(
            [
                RaceSession(race_id=race.id, type="R", starts_at=NOW + timedelta(minutes=3)),
                RaceSession(
                    race_id=race.id, type="Q", starts_at=NOW - timedelta(days=1), status="cancelled"
                ),
            ]
        )
        await s.commit()
        return race.id


async def test_tick_marks_live_resolves_key_and_enqueues_poll(
    session_factory: async_sessionmaker[AsyncSession], race_id: uuid.UUID
) -> None:
    arq = FakeArq()
    openf1 = FakeOpenF1(
        [
            {
                "session_key": 111,
                "session_name": "Race",
                "year": 2025,
                "date_start": "2024-03-24T04:00:00+00:00",
                "date_end": "2024-03-24T06:00:00+00:00",
            },
            {
                "session_key": 9693,
                "session_name": "Race",
                "year": 2025,
                "date_start": "2025-03-16T04:03:00+00:00",
                "date_end": "2025-03-16T05:45:00+00:00",
            },
        ]
    )
    ctx = {"session_factory": session_factory, "redis": arq, "openf1": openf1}
    await tick_sessions(ctx, now=NOW)
    async with session_factory() as s:
        r = (await s.execute(select(RaceSession).where(RaceSession.type == "R"))).scalar_one()
        q = (await s.execute(select(RaceSession).where(RaceSession.type == "Q"))).scalar_one()
    assert (r.status, r.openf1_session_key) == ("live", 9693)
    assert r.ends_at == datetime(2025, 3, 16, 5, 45, tzinfo=UTC)
    assert q.status == "cancelled"
    assert arq.jobs == [("poll_live_session", (9693,), {"_job_id": "live:9693"})]

    await tick_sessions(ctx, now=NOW + timedelta(minutes=1))  # key cached: no new lookup
    assert openf1.calls == 1

    await tick_sessions(ctx, now=datetime(2025, 3, 16, 5, 46, tzinfo=UTC))
    async with session_factory() as s:
        r = (await s.execute(select(RaceSession).where(RaceSession.type == "R"))).scalar_one()
    assert r.status == "finished"
    name, args, kwargs = arq.jobs[-1]
    assert (name, args, kwargs["_job_id"]) == ("flush_live_session", (r.id,), f"flush:{r.id}")
    assert kwargs["_defer_by"] == timedelta(minutes=45)


async def test_tick_skips_openf1_when_nothing_is_near(
    session_factory: async_sessionmaker[AsyncSession], race_id: uuid.UUID
) -> None:
    openf1 = FakeOpenF1([])
    ctx = {"session_factory": session_factory, "redis": FakeArq(), "openf1": openf1}
    await tick_sessions(ctx, now=NOW - timedelta(hours=2))
    assert openf1.calls == 0


async def test_rounds_needing_results(session_factory: async_sessionmaker[AsyncSession]) -> None:
    from f1_db.models import Driver, SessionResult, Team
    from f1_worker.scheduling import rounds_needing_results

    async with session_factory() as s:
        await s.execute(text("truncate seasons, drivers, teams cascade"))
        season = Season(year=1994)
        team = Team(ref="t", name="T")
        drivers = [Driver(ref=f"d{i}", given_name="A", family_name=f"D{i}") for i in range(3)]
        s.add_all([season, team, *drivers])
        await s.flush()
        races = [
            Race(
                season_id=season.id,
                round=n,
                name=f"GP{n}",
                circuit_name="C",
                race_date=date(1994, 3, n),
            )
            for n in (1, 2, 3, 4)
        ]
        s.add_all(races)
        await s.flush()
        for race, status in zip(
            races, ["finished", "finished", "finished", "scheduled"], strict=True
        ):
            s.add(
                RaceSession(
                    race_id=race.id,
                    type="R",
                    status=status,
                    starts_at=datetime(1994, 3, race.round, 14, tzinfo=UTC),
                )
            )
        for race, n in ((races[0], 3), (races[1], 2)):  # round 1 complete, round 2 partial
            for d in drivers[:n]:
                s.add(
                    SessionResult(
                        race_id=race.id,
                        session_type="R",
                        driver_id=d.id,
                        team_id=team.id,
                        position=None,
                        status="Finished",
                    )
                )
        await s.commit()
    assert await rounds_needing_results(session_factory, 1994) == [2, 3]


async def test_races_needing_weather(session_factory: async_sessionmaker[AsyncSession]) -> None:
    from f1_worker.scheduling import races_needing_weather

    async with session_factory() as s:
        await s.execute(text("truncate seasons cascade"))
        season = Season(year=1993)
        s.add(season)
        await s.flush()
        s.add_all(
            [
                Race(
                    season_id=season.id,
                    round=n,
                    name=f"GP{n}",
                    circuit_name="C",
                    race_date=date(1993, 3, day),
                )
                for n, day in ((1, 1), (2, 10), (3, 16), (4, 30))
            ]
        )
        await s.commit()
    found = await races_needing_weather(session_factory, date(1993, 3, 9))
    async with session_factory() as s:
        rounds = sorted(
            (await s.execute(select(Race.round).where(Race.id.in_(found)))).scalars().all()
        )
    assert rounds == [2, 3]  # within the next 7 days, inclusive
