from f1_db.models import ConstructorStanding, Driver, DriverStanding, Season, Team
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.schemas.standings import (
    ConstructorStandingOut,
    DriverRef,
    DriverStandingOut,
    TeamRef,
)


class StandingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def latest_season_with_data(self) -> int | None:
        stmt = select(func.max(Season.year)).join(
            DriverStanding, DriverStanding.season_id == Season.id
        )
        year: int | None = (await self.session.execute(stmt)).scalar()
        return year

    async def latest_driver_standings(self, year: int) -> list[DriverStandingOut]:
        latest_round = (
            select(func.max(DriverStanding.round))
            .join(Season, Season.id == DriverStanding.season_id)
            .where(Season.year == year)
            .scalar_subquery()
        )
        stmt = (
            select(DriverStanding, Driver, Team)
            .join(Season, Season.id == DriverStanding.season_id)
            .join(Driver, Driver.id == DriverStanding.driver_id)
            .join(Team, Team.id == DriverStanding.team_id)
            .where(Season.year == year, DriverStanding.round == latest_round)
            .order_by(DriverStanding.position)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            DriverStandingOut(
                position=s.position,
                points=float(s.points),
                wins=s.wins,
                driver=DriverRef.of(d),
                team=TeamRef.of(t),
                season=year,
                round=s.round,
                updated_at=s.ingested_at,
            )
            for s, d, t in rows
        ]

    async def latest_season_with_constructor_data(self) -> int | None:
        stmt = select(func.max(Season.year)).join(
            ConstructorStanding, ConstructorStanding.season_id == Season.id
        )
        year: int | None = (await self.session.execute(stmt)).scalar()
        return year

    async def latest_constructor_standings(self, year: int) -> list[ConstructorStandingOut]:
        latest_round = (
            select(func.max(ConstructorStanding.round))
            .join(Season, Season.id == ConstructorStanding.season_id)
            .where(Season.year == year)
            .scalar_subquery()
        )
        stmt = (
            select(ConstructorStanding, Team)
            .join(Season, Season.id == ConstructorStanding.season_id)
            .join(Team, Team.id == ConstructorStanding.team_id)
            .where(Season.year == year, ConstructorStanding.round == latest_round)
            .order_by(ConstructorStanding.position)
        )
        return [
            ConstructorStandingOut(
                position=c.position,
                points=float(c.points),
                wins=c.wins,
                team=TeamRef.of(t),
                season=year,
                round=c.round,
                updated_at=c.ingested_at,
            )
            for c, t in (await self.session.execute(stmt)).all()
        ]
