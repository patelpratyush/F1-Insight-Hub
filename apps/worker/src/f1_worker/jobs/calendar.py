from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import Circuit, Race, RaceSession, Season
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_worker.runs import record_run
from f1_worker.sources.jolpica import JolpicaClient

SOURCE = "jolpica"


async def ingest_calendar(
    session_factory: async_sessionmaker[AsyncSession], client: JolpicaClient, year: int
) -> int:
    async with record_run(session_factory, "calendar") as run:
        races = await client.calendar(year)
        if not races:
            return 0
        async with session_factory() as s:
            await s.execute(
                insert(Season)
                .values(id=uuid7(), year=year)
                .on_conflict_do_nothing(index_elements=["year"])
            )
            season_id = (await s.execute(select(Season.id).where(Season.year == year))).scalar_one()
            for r in races:
                await s.execute(
                    insert(Circuit)
                    .values(
                        id=uuid7(),
                        ref=r.circuit_ref,
                        name=r.circuit_name,
                        locality=r.locality,
                        country=r.country,
                        lat=r.lat,
                        lon=r.lon,
                        source=SOURCE,
                        ingested_at=utcnow(),
                    )
                    .on_conflict_do_update(index_elements=["ref"], set_={"name": r.circuit_name})
                )
                circuit_id = (
                    await s.execute(select(Circuit.id).where(Circuit.ref == r.circuit_ref))
                ).scalar_one()
                await s.execute(
                    insert(Race)
                    .values(
                        id=uuid7(),
                        season_id=season_id,
                        round=r.round,
                        name=r.name,
                        circuit_name=r.circuit_name,
                        race_date=r.race_date,
                        circuit_id=circuit_id,
                        source=SOURCE,
                        ingested_at=utcnow(),
                    )
                    .on_conflict_do_update(
                        index_elements=["season_id", "round"],
                        set_={"name": r.name, "race_date": r.race_date, "circuit_id": circuit_id},
                    )
                )
                race_id = (
                    await s.execute(
                        select(Race.id).where(Race.season_id == season_id, Race.round == r.round)
                    )
                ).scalar_one()
                for stype, starts in r.sessions.items():
                    # Only the start time is refreshed; status (live/finished/cancelled) is kept.
                    await s.execute(
                        insert(RaceSession)
                        .values(
                            id=uuid7(),
                            race_id=race_id,
                            type=stype,
                            starts_at=starts,
                            status="scheduled",
                            source=SOURCE,
                            ingested_at=utcnow(),
                        )
                        .on_conflict_do_update(
                            index_elements=["race_id", "type"], set_={"starts_at": starts}
                        )
                    )
            await s.commit()
        run.rows = len(races)
        return len(races)
