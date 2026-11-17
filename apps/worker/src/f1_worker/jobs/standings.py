from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import Driver, DriverStanding, Season, Team
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_worker.runs import record_run
from f1_worker.sources.jolpica import JolpicaClient

SOURCE = "jolpica"


async def ingest_driver_standings(
    session_factory: async_sessionmaker[AsyncSession], client: JolpicaClient, year: int
) -> int:
    async with record_run(session_factory, "standings") as run:
        rows = await client.driver_standings(year)
        if not rows:
            run.rows = 0
            return 0
        async with session_factory() as s:
            await s.execute(
                insert(Season)
                .values(id=uuid7(), year=year)
                .on_conflict_do_nothing(index_elements=["year"])
            )
            season_id = (await s.execute(select(Season.id).where(Season.year == year))).scalar_one()
            for r in rows:
                await s.execute(
                    insert(Team)
                    .values(
                        id=uuid7(),
                        ref=r.team_ref,
                        name=r.team_name,
                        nationality=r.team_nationality,
                        source=SOURCE,
                        ingested_at=utcnow(),
                    )
                    .on_conflict_do_update(
                        index_elements=["ref"],
                        set_={"name": r.team_name, "nationality": r.team_nationality},
                    )
                )
                await s.execute(
                    insert(Driver)
                    .values(
                        id=uuid7(),
                        ref=r.driver_ref,
                        code=r.driver_code,
                        given_name=r.given_name,
                        family_name=r.family_name,
                        number=r.number,
                        nationality=r.driver_nationality,
                        source=SOURCE,
                        ingested_at=utcnow(),
                    )
                    .on_conflict_do_update(
                        index_elements=["ref"],
                        set_={
                            "code": r.driver_code,
                            "number": r.number,
                            "given_name": r.given_name,
                            "family_name": r.family_name,
                        },
                    )
                )
                driver_id = (
                    await s.execute(select(Driver.id).where(Driver.ref == r.driver_ref))
                ).scalar_one()
                team_id = (
                    await s.execute(select(Team.id).where(Team.ref == r.team_ref))
                ).scalar_one()
                stmt = insert(DriverStanding).values(
                    id=uuid7(),
                    season_id=season_id,
                    round=r.round,
                    driver_id=driver_id,
                    team_id=team_id,
                    position=r.position,
                    points=r.points,
                    wins=r.wins,
                    source=SOURCE,
                    ingested_at=utcnow(),
                )
                await s.execute(
                    stmt.on_conflict_do_update(
                        index_elements=["season_id", "round", "driver_id"],
                        set_={
                            "position": r.position,
                            "points": r.points,
                            "wins": r.wins,
                            "team_id": team_id,
                            "ingested_at": utcnow(),
                        },
                    )
                )
            await s.commit()
        run.rows = len(rows)
        return len(rows)
