from f1_db.models import Circuit, Race, RaceSession, Season
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.schemas.calendar import CircuitOut, RaceSummary, SessionOut


class CalendarService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def latest_season_with_races(self) -> int | None:
        stmt = select(func.max(Season.year)).join(Race, Race.season_id == Season.id)
        year: int | None = (await self.session.execute(stmt)).scalar()
        return year

    async def summaries(self, year: int, rnd: int | None = None) -> list[RaceSummary]:
        stmt = (
            select(Race, Circuit)
            .join(Season, Season.id == Race.season_id)
            .outerjoin(Circuit, Circuit.id == Race.circuit_id)
            .where(Season.year == year)
            .order_by(Race.round)
        )
        if rnd is not None:
            stmt = stmt.where(Race.round == rnd)
        rows = (await self.session.execute(stmt)).all()
        if not rows:
            return []
        sessions = (
            (
                await self.session.execute(
                    select(RaceSession)
                    .where(RaceSession.race_id.in_([r.id for r, _ in rows]))
                    .order_by(RaceSession.starts_at)
                )
            )
            .scalars()
            .all()
        )
        by_race: dict[object, list[SessionOut]] = {}
        for s in sessions:
            by_race.setdefault(s.race_id, []).append(
                SessionOut(
                    type=s.type,
                    starts_at=s.starts_at,
                    status=s.status,
                    openf1_session_key=s.openf1_session_key,
                )
            )
        return [
            RaceSummary(
                season=year,
                round=r.round,
                name=r.name,
                circuit=None
                if c is None
                else CircuitOut(
                    ref=c.ref,
                    name=c.name,
                    locality=c.locality,
                    country=c.country,
                    lat=c.lat,
                    lon=c.lon,
                ),
                race_date=r.race_date,
                sessions=by_race.get(r.id, []),
            )
            for r, c in rows
        ]
