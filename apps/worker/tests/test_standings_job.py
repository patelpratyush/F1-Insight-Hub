import asyncio
import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import respx
from f1_db.models import Driver, DriverStanding, IngestionRun
from f1_worker.jobs.standings import ingest_driver_standings
from f1_worker.resilience import CircuitBreaker, CircuitOpenError
from f1_worker.sources.jolpica import JolpicaClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "driver_standings_2025.json").read_text()
)
URL = "https://api.jolpi.ca/ergast/f1/2025/driverStandings.json"


@pytest.fixture(autouse=True)
async def clean(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        await s.execute(
            text("truncate driver_standings, drivers, teams, seasons, ingestion_runs cascade")
        )
        await s.commit()


@respx.mock
async def test_ingest_writes_rows_and_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    first = await ingest_driver_standings(session_factory, JolpicaClient(), 2025)
    second = await ingest_driver_standings(session_factory, JolpicaClient(), 2025)
    assert first == second == 2
    async with session_factory() as s:
        count = (await s.execute(select(func.count()).select_from(DriverStanding))).scalar_one()
    assert count == 2


@respx.mock
async def test_concurrent_runs_do_not_duplicate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    await asyncio.gather(
        *[ingest_driver_standings(session_factory, JolpicaClient(), 2025) for _ in range(5)]
    )
    async with session_factory() as s:
        count = (await s.execute(select(func.count()).select_from(DriverStanding))).scalar_one()
        drivers = (await s.execute(select(func.count()).select_from(Driver))).scalar_one()
        points = (
            await s.execute(
                select(DriverStanding.points)
                .join(Driver, Driver.id == DriverStanding.driver_id)
                .where(Driver.ref == "norris")
            )
        ).scalar_one()
    assert count == 2
    assert drivers == 2
    assert points == Decimal("423.50")


@respx.mock
async def test_empty_upstream_writes_nothing_and_succeeds(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    empty = {"MRData": {"StandingsTable": {"season": "2025", "StandingsLists": []}}}
    respx.get(URL).mock(return_value=httpx.Response(200, json=empty))
    assert await ingest_driver_standings(session_factory, JolpicaClient(), 2025) == 0
    async with session_factory() as s:
        run = (await s.execute(select(IngestionRun))).scalar_one()
        count = (await s.execute(select(func.count()).select_from(DriverStanding))).scalar_one()
    assert run.status == "success" and run.rows == 0
    assert count == 0


@respx.mock
async def test_upstream_failure_records_failed_run(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await ingest_driver_standings(session_factory, JolpicaClient(retry_wait=0), 2025)
    async with session_factory() as s:
        run = (await s.execute(select(IngestionRun))).scalar_one()
    assert run.status == "failed"


@respx.mock
async def test_repeated_outage_opens_circuit_and_keeps_last_good_data(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    client = JolpicaClient(retry_wait=0, breaker=CircuitBreaker(2, reset_seconds=60))
    assert await ingest_driver_standings(session_factory, client, 2025) == 2

    route.mock(return_value=httpx.Response(429))
    for _ in range(2):
        with pytest.raises(httpx.HTTPStatusError):
            await ingest_driver_standings(session_factory, client, 2025)
    calls_before = route.call_count
    with pytest.raises(CircuitOpenError):
        await ingest_driver_standings(session_factory, client, 2025)
    assert route.call_count == calls_before  # open circuit makes no upstream call

    async with session_factory() as s:
        statuses = (
            (await s.execute(select(IngestionRun.status).order_by(IngestionRun.started_at)))
            .scalars()
            .all()
        )
        count = (await s.execute(select(func.count()).select_from(DriverStanding))).scalar_one()
    assert statuses == ["success", "failed", "failed", "failed"]
    assert count == 2
