import uuid
from datetime import timedelta

from f1_core.ids import uuid7
from f1_db.models import Circuit, Race, WeatherSample
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_worker.runs import record_run
from f1_worker.sources.openmeteo import OpenMeteoClient

SOURCE = "open-meteo"


async def ingest_weather(
    session_factory: async_sessionmaker[AsyncSession], client: OpenMeteoClient, race_id: uuid.UUID
) -> int:
    """Hourly forecast for Friday to Sunday of the race weekend. Track temperature stays
    None here; OpenF1 provides it live."""
    async with record_run(session_factory, "weather") as run:
        async with session_factory() as s:
            row = (
                await s.execute(
                    select(Race.race_date, Circuit.lat, Circuit.lon)
                    .join(Circuit, Circuit.id == Race.circuit_id)
                    .where(Race.id == race_id)
                )
            ).one_or_none()
        if row is None:  # race unknown or has no circuit yet
            return 0
        race_date, lat, lon = row
        points = await client.forecast(lat, lon, race_date - timedelta(days=2), race_date)
        if not points:
            return 0
        async with session_factory() as s:
            for p in points:
                values = {
                    "air_temp_c": p.air_temp_c,
                    "humidity": p.humidity,
                    "wind_kph": p.wind_kph,
                    "rain_probability": p.rain_probability,
                }
                await s.execute(
                    insert(WeatherSample)
                    .values(
                        id=uuid7(),
                        race_id=race_id,
                        observed_at=p.observed_at,
                        track_temp_c=None,
                        source=SOURCE,
                        **values,
                    )
                    .on_conflict_do_update(
                        index_elements=["race_id", "observed_at", "source"], set_=values
                    )
                )
            await s.commit()
        run.rows = len(points)
        return len(points)
