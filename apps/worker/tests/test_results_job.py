import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import respx
from f1_db.models import Driver, DriverTeamStint, Race, Season, SessionResult, Team
from f1_worker.jobs.results import ingest_results
from f1_worker.sources.jolpica import JolpicaClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

FIX = Path(__file__).parent / "fixtures"
BASE = "https://api.jolpi.ca/ergast/f1/2025"
EMPTY: dict[str, object] = {"MRData": {"RaceTable": {"Races": []}}}


def _mock_round(rnd: int) -> None:
    data = json.loads((FIX / f"race_results_2025_{rnd}.json").read_text())
    respx.get(f"{BASE}/{rnd}/results.json").mock(return_value=httpx.Response(200, json=data))
    respx.get(f"{BASE}/{rnd}/qualifying.json").mock(return_value=httpx.Response(200, json=EMPTY))
    respx.get(f"{BASE}/{rnd}/sprint.json").mock(return_value=httpx.Response(200, json=EMPTY))


@pytest.fixture(autouse=True)
async def races(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        await s.execute(
            text(
                "truncate session_results, driver_team_stints, race_sessions, races,"
                " driver_standings, drivers, teams, seasons, ingestion_runs cascade"
            )
        )
        season = Season(year=2025)
        s.add(season)
        await s.flush()
        for rnd in (1, 6):
            s.add(
                Race(
                    season_id=season.id,
                    round=rnd,
                    name=f"GP {rnd}",
                    circuit_name="C",
                    race_date=date(2025, 3, 10 + rnd),
                )
            )
        await s.commit()


async def _stints(s: AsyncSession, ref: str) -> list[tuple[int, int | None, str]]:
    rows = await s.execute(
        select(DriverTeamStint.from_round, DriverTeamStint.to_round, Team.ref)
        .join(Driver, Driver.id == DriverTeamStint.driver_id)
        .join(Team, Team.id == DriverTeamStint.team_id)
        .where(Driver.ref == ref)
        .order_by(DriverTeamStint.from_round)
    )
    return [(a, b, c) for a, b, c in rows.all()]


@respx.mock
async def test_team_change_creates_new_stint(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    _mock_round(1)
    _mock_round(6)
    client = JolpicaClient()
    await ingest_results(session_factory, client, 2025, 1)
    await ingest_results(session_factory, client, 2025, 6)
    async with session_factory() as s:
        assert await _stints(s, "lawson") == [(1, 5, "red_bull"), (6, None, "rb")]
        assert await _stints(s, "max_verstappen") == [(1, None, "red_bull")]
        teams = (
            await s.execute(
                select(Race.round, Team.ref)
                .join(SessionResult, SessionResult.race_id == Race.id)
                .join(Driver, Driver.id == SessionResult.driver_id)
                .join(Team, Team.id == SessionResult.team_id)
                .where(Driver.ref == "lawson")
                .order_by(Race.round)
            )
        ).all()
    assert [tuple(t) for t in teams] == [(1, "red_bull"), (6, "rb")]


@respx.mock
async def test_results_idempotent_and_dnf_has_null_position(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    _mock_round(1)
    client = JolpicaClient()
    assert await ingest_results(session_factory, client, 2025, 1) == 3
    assert await ingest_results(session_factory, client, 2025, 1) == 3
    async with session_factory() as s:
        count = (await s.execute(select(func.count()).select_from(SessionResult))).scalar_one()
        dnf = (
            await s.execute(
                select(SessionResult)
                .join(Driver, Driver.id == SessionResult.driver_id)
                .where(Driver.ref == "norris")
            )
        ).scalar_one()
        stints = (await s.execute(select(func.count()).select_from(DriverTeamStint))).scalar_one()
    assert count == 3
    assert dnf.position is None and dnf.status == "Retired" and dnf.grid == 1
    assert dnf.session_type == "R" and dnf.time_ms is None
    assert stints == 3


@respx.mock
async def test_fractional_points_preserved(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    _mock_round(1)
    _mock_round(6)
    client = JolpicaClient()
    await ingest_results(session_factory, client, 2025, 1)
    await ingest_results(session_factory, client, 2025, 6)
    async with session_factory() as s:
        pts = (
            await s.execute(
                select(SessionResult.points)
                .join(Race, Race.id == SessionResult.race_id)
                .join(Driver, Driver.id == SessionResult.driver_id)
                .where(Driver.ref == "lawson", Race.round == 6)
            )
        ).scalar_one()
    assert pts == Decimal("0.50")


@respx.mock
async def test_round_without_results_or_race_is_noop(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    for kind in ("results", "qualifying", "sprint"):
        respx.get(f"{BASE}/9/{kind}.json").mock(return_value=httpx.Response(200, json=EMPTY))
    assert await ingest_results(session_factory, JolpicaClient(), 2025, 9) == 0
