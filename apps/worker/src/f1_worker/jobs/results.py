import uuid

from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import DriverTeamStint, Race, Season, SessionResult
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_worker.jobs._upserts import SOURCE, upsert_driver, upsert_team
from f1_worker.runs import record_run
from f1_worker.sources.jolpica import JolpicaClient


async def sync_stint(
    s: AsyncSession, season_id: uuid.UUID, driver_id: uuid.UUID, team_id: uuid.UUID, rnd: int
) -> None:
    # shortcut: assumes rounds are ingested in order; re-run the season in order to repair
    # stints if an earlier round is ingested after a later one.
    open_stint = (
        await s.execute(
            select(DriverTeamStint).where(
                DriverTeamStint.season_id == season_id,
                DriverTeamStint.driver_id == driver_id,
                DriverTeamStint.to_round.is_(None),
            )
        )
    ).scalar_one_or_none()
    if open_stint is None:
        s.add(
            DriverTeamStint(
                season_id=season_id,
                driver_id=driver_id,
                team_id=team_id,
                from_round=1 if rnd <= 1 else rnd,
                source=SOURCE,
            )
        )
    elif open_stint.team_id != team_id:
        open_stint.to_round = rnd - 1
        s.add(
            DriverTeamStint(
                season_id=season_id,
                driver_id=driver_id,
                team_id=team_id,
                from_round=rnd,
                source=SOURCE,
            )
        )


async def ingest_results(
    session_factory: async_sessionmaker[AsyncSession], client: JolpicaClient, year: int, rnd: int
) -> int:
    """Race, qualifying and sprint results for one round. The race must already exist
    (created by the calendar job); otherwise nothing is written."""
    async with record_run(session_factory, "results") as run:
        rows = [
            *await client.results(year, rnd),
            *await client.qualifying(year, rnd),
            *await client.sprint(year, rnd),
        ]
        if not rows:
            return 0
        async with session_factory() as s:
            race = (
                await s.execute(
                    select(Race.id, Race.season_id)
                    .join(Season, Season.id == Race.season_id)
                    .where(Season.year == year, Race.round == rnd)
                )
            ).one_or_none()
            if race is None:
                return 0
            race_id, season_id = race
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
                values = {
                    "team_id": team_id,
                    "position": r.position,
                    "grid": r.grid,
                    "status": r.status,
                    "points": r.points,
                    "time_ms": r.time_ms,
                }
                await s.execute(
                    insert(SessionResult)
                    .values(
                        id=uuid7(),
                        race_id=race_id,
                        session_type=r.session_type,
                        driver_id=driver_id,
                        source=SOURCE,
                        ingested_at=utcnow(),
                        **values,
                    )
                    .on_conflict_do_update(
                        index_elements=["race_id", "session_type", "driver_id"],
                        set_={**values, "ingested_at": utcnow()},
                    )
                )
                if r.session_type == "R":
                    await sync_stint(s, season_id, driver_id, team_id, rnd)
            await s.commit()
        run.rows = len(rows)
        return len(rows)
