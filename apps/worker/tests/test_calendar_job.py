import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx
from f1_db.models import Race, RaceSession
from f1_worker.jobs.calendar import ingest_calendar
from f1_worker.sources.jolpica import JolpicaClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "calendar_2025.json").read_text())
URL = "https://api.jolpi.ca/ergast/f1/2025.json"


@pytest.fixture(autouse=True)
async def clean(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        await s.execute(text("truncate race_sessions, races, circuits, seasons cascade"))
        await s.commit()


@respx.mock
async def test_parses_sessions_per_weekend_format() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    races = await JolpicaClient().calendar(2025)
    assert set(races[0].sessions) == {"FP1", "FP2", "FP3", "Q", "R"}
    assert set(races[1].sessions) == {"FP1", "SQ", "SPRINT", "Q", "R"}
    assert races[0].sessions["R"] == datetime(2025, 3, 16, 4, 0, tzinfo=UTC)


@respx.mock
async def test_ingest_is_idempotent(session_factory: async_sessionmaker[AsyncSession]) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    assert await ingest_calendar(session_factory, JolpicaClient(), 2025) == 2
    assert await ingest_calendar(session_factory, JolpicaClient(), 2025) == 2
    async with session_factory() as s:
        races = (await s.execute(select(func.count()).select_from(Race))).scalar_one()
        sessions = (await s.execute(select(func.count()).select_from(RaceSession))).scalar_one()
    assert races == 2 and sessions == 10  # 5 per weekend in the fixture


@respx.mock
async def test_reingest_keeps_session_status(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    await ingest_calendar(session_factory, JolpicaClient(), 2025)
    async with session_factory() as s:
        await s.execute(text("update race_sessions set status = 'cancelled' where type = 'SPRINT'"))
        await s.commit()
    await ingest_calendar(session_factory, JolpicaClient(), 2025)
    async with session_factory() as s:
        status = (
            await s.execute(select(RaceSession.status).where(RaceSession.type == "SPRINT"))
        ).scalar_one()
    assert status == "cancelled"


@respx.mock
async def test_empty_calendar_is_noop(session_factory: async_sessionmaker[AsyncSession]) -> None:
    empty = {"MRData": {"RaceTable": {"season": "2030", "Races": []}}}
    respx.get("https://api.jolpi.ca/ergast/f1/2030.json").mock(
        return_value=httpx.Response(200, json=empty)
    )
    assert await ingest_calendar(session_factory, JolpicaClient(), 2030) == 0
