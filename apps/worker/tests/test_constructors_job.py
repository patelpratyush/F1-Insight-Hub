import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import respx
from f1_db.models import ConstructorStanding, Team
from f1_worker.jobs.constructors import ingest_constructor_standings
from f1_worker.sources.jolpica import JolpicaClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "constructor_standings_2025.json").read_text()
)
URL = "https://api.jolpi.ca/ergast/f1/2025/constructorStandings.json"


@pytest.fixture(autouse=True)
async def clean(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        await s.execute(text("truncate constructor_standings, teams, seasons cascade"))
        await s.commit()


@respx.mock
async def test_ingest_idempotent_with_fractional_points(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    client = JolpicaClient()
    assert await ingest_constructor_standings(session_factory, client, 2025) == 2
    assert await ingest_constructor_standings(session_factory, client, 2025) == 2
    async with session_factory() as s:
        count = (
            await s.execute(select(func.count()).select_from(ConstructorStanding))
        ).scalar_one()
        mcl = (
            await s.execute(
                select(ConstructorStanding)
                .join(Team, Team.id == ConstructorStanding.team_id)
                .where(Team.ref == "mclaren")
            )
        ).scalar_one()
    assert count == 2
    assert (mcl.position, mcl.points, mcl.wins, mcl.round) == (1, Decimal("143.50"), 2, 6)


@respx.mock
async def test_empty_standings_is_noop(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    empty = {"MRData": {"StandingsTable": {"season": "2025", "StandingsLists": []}}}
    respx.get(URL).mock(return_value=httpx.Response(200, json=empty))
    assert await ingest_constructor_standings(session_factory, JolpicaClient(), 2025) == 0
