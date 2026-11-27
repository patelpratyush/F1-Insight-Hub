from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import ConstructorStanding
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_worker.jobs._upserts import SOURCE, upsert_season, upsert_team
from f1_worker.runs import record_run
from f1_worker.sources.jolpica import JolpicaClient


async def ingest_constructor_standings(
    session_factory: async_sessionmaker[AsyncSession], client: JolpicaClient, year: int
) -> int:
    async with record_run(session_factory, "constructors") as run:
        rows = await client.constructor_standings(year)
        if not rows:
            return 0
        async with session_factory() as s:
            season_id = await upsert_season(s, year)
            for r in rows:
                team_id = await upsert_team(s, r.team_ref, r.team_name, r.team_nationality)
                values = {"position": r.position, "points": r.points, "wins": r.wins}
                await s.execute(
                    insert(ConstructorStanding)
                    .values(
                        id=uuid7(),
                        season_id=season_id,
                        round=r.round,
                        team_id=team_id,
                        source=SOURCE,
                        ingested_at=utcnow(),
                        **values,
                    )
                    .on_conflict_do_update(
                        index_elements=["season_id", "round", "team_id"],
                        set_={**values, "ingested_at": utcnow()},
                    )
                )
            await s.commit()
        run.rows = len(rows)
        return len(rows)
