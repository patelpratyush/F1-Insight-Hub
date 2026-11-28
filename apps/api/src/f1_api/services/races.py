from typing import Any

from f1_db.models import Driver, Race, Season, SessionResult, Team, WeatherSample
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.schemas.races import RaceDetail, ResultRow, WeatherOut
from f1_api.schemas.standings import DriverRef, TeamRef
from f1_api.services.calendar import CalendarService

SESSION_TYPES = ("R", "Q", "SPRINT")


def result_rows_stmt(*where: Any) -> Any:
    """Results joined with the driver and the team they drove for in that session."""
    return (
        select(SessionResult, Driver, Team)
        .join(Driver, Driver.id == SessionResult.driver_id)
        .join(Team, Team.id == SessionResult.team_id)
        .where(*where)
    )


def to_row(r: SessionResult, d: Driver, t: Team) -> ResultRow:
    return ResultRow(
        position=r.position,
        grid=r.grid,
        status=r.status or "",
        points=float(r.points),
        time_ms=r.time_ms,
        driver=DriverRef.of(d),
        team=TeamRef.of(t),
    )


class RaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def detail(self, year: int, rnd: int) -> RaceDetail | None:
        summaries = await CalendarService(self.session).summaries(year, rnd)
        if not summaries:
            return None
        race_id = (
            await self.session.execute(
                select(Race.id)
                .join(Season, Season.id == Race.season_id)
                .where(Season.year == year, Race.round == rnd)
            )
        ).scalar_one()
        weather = (
            (
                await self.session.execute(
                    select(WeatherSample)
                    .where(WeatherSample.race_id == race_id)
                    .order_by(WeatherSample.observed_at)
                )
            )
            .scalars()
            .all()
        )
        rows = (
            await self.session.execute(
                result_rows_stmt(SessionResult.race_id == race_id).order_by(
                    SessionResult.position.asc().nulls_last(), SessionResult.grid
                )
            )
        ).all()
        results: dict[str, list[ResultRow]] = {t: [] for t in SESSION_TYPES}
        for r, d, t in rows:
            results.setdefault(r.session_type, []).append(to_row(r, d, t))
        return RaceDetail(
            **summaries[0].model_dump(),
            weather=[
                WeatherOut(
                    observed_at=w.observed_at,
                    air_temp_c=w.air_temp_c,
                    track_temp_c=w.track_temp_c,
                    humidity=w.humidity,
                    wind_kph=w.wind_kph,
                    rain_probability=w.rain_probability,
                    source=w.source,
                )
                for w in weather
            ],
            results=results,
        )
