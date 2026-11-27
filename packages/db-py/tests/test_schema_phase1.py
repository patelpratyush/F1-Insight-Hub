from datetime import UTC, datetime

import pytest
from f1_db.models import Circuit, Race, RaceSession, Season
from f1_db.session import make_session_factory
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

EXPECTED = {
    "circuits",
    "race_sessions",
    "weather_samples",
    "constructor_standings",
    "driver_team_stints",
    "laps",
    "pit_stops",
    "stints",
}


async def test_tables_exist(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert names >= EXPECTED


async def test_race_session_unique_per_race_and_type(engine: AsyncEngine) -> None:
    factory = make_session_factory(engine)
    async with factory() as s:
        season = Season(year=2098)
        circuit = Circuit(ref="c1", name="C", locality="L", country="X", lat=1.0, lon=2.0)
        s.add_all([season, circuit])
        await s.flush()
        race = Race(
            season_id=season.id,
            round=1,
            name="GP",
            circuit_name="C",
            race_date=datetime(2098, 3, 1).date(),
            circuit_id=circuit.id,
        )
        s.add(race)
        await s.flush()
        when = datetime(2098, 3, 1, 14, tzinfo=UTC)
        s.add(RaceSession(race_id=race.id, type="R", starts_at=when, status="scheduled"))
        await s.commit()
        s.add(RaceSession(race_id=race.id, type="R", starts_at=when, status="scheduled"))
        with pytest.raises(IntegrityError):
            await s.commit()
