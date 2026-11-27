from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import DriverStanding
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_worker.jobs._upserts import SOURCE, upsert_driver, upsert_season, upsert_team
from f1_worker.runs import record_run
from f1_worker.sources.jolpica import JolpicaClient


async def ingest_driver_standings(
    session_factory: async_sessionmaker[AsyncSession], client: JolpicaClient, year: int
) -> int:
    async with record_run(session_factory, "standings") as run:
        rows = await client.driver_standings(year)
        if not rows:
            run.rows = 0
            return 0
        async with session_factory() as s:
            season_id = await upsert_season(s, year)
            for r in rows:
                team_id = await upsert_team(s, r.team_ref, r.team_name, r.team_nationality)
                driver_id = await upsert_driver(
                    s,
                    r.driver_ref,
                    r.driver_code,
                    r.given_name,
                    r.family_name,
                    r.number,
                    r.driver_nationality,
                )
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
