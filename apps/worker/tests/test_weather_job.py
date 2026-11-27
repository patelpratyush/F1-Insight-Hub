import json
import uuid
from datetime import date
from pathlib import Path

import httpx
import pytest
import respx
from f1_db.models import Circuit, Race, Season, WeatherSample
from f1_worker.jobs.weather import ingest_weather
from f1_worker.sources.openmeteo import OpenMeteoClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "openmeteo_albert_park.json").read_text()
)
URL = "https://api.open-meteo.com/v1/forecast"


@pytest.fixture
async def race_id(session_factory: async_sessionmaker[AsyncSession]) -> object:
    async with session_factory() as s:
        await s.execute(text("truncate weather_samples, races, circuits, seasons cascade"))
        season = Season(year=2025)
        circuit = Circuit(
            ref="albert_park",
            name="Albert Park",
            locality="Melbourne",
            country="Australia",
            lat=-37.8497,
            lon=144.968,
        )
        s.add_all([season, circuit])
        await s.flush()
        race = Race(
            season_id=season.id,
            round=1,
            name="Australian GP",
            circuit_name="Albert Park",
            race_date=date(2025, 3, 16),
            circuit_id=circuit.id,
        )
        s.add(race)
        await s.commit()
        return race.id


@respx.mock
async def test_parses_hourly_points() -> None:
    route = respx.get(url__startswith=URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    pts = await OpenMeteoClient().forecast(-37.8497, 144.968, date(2025, 3, 14), date(2025, 3, 16))
    assert len(pts) == 6
    assert pts[0].observed_at.tzinfo is not None
    assert pts[0].rain_probability == 20.0
    assert pts[0].air_temp_c == 18.2
    params = route.calls[0].request.url.params
    assert params["timezone"] == "UTC" and params["start_date"] == "2025-03-14"


@respx.mock
async def test_null_values_become_none() -> None:
    respx.get(url__startswith=URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    pts = await OpenMeteoClient().forecast(0.0, 0.0, date(2025, 3, 14), date(2025, 3, 16))
    assert pts[1].rain_probability is None
    assert pts[3].air_temp_c is None


@respx.mock
async def test_ingest_weather_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession], race_id: uuid.UUID
) -> None:
    route = respx.get(url__startswith=URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    client = OpenMeteoClient()
    assert await ingest_weather(session_factory, client, race_id) == 6
    assert await ingest_weather(session_factory, client, race_id) == 6
    async with session_factory() as s:
        count = (await s.execute(select(func.count()).select_from(WeatherSample))).scalar_one()
        track = (await s.execute(select(WeatherSample.track_temp_c).limit(1))).scalar_one()
        source = (await s.execute(select(WeatherSample.source).limit(1))).scalar_one()
    assert count == 6 and track is None and source == "open-meteo"
    params = route.calls[0].request.url.params
    assert (params["start_date"], params["end_date"]) == ("2025-03-14", "2025-03-16")
