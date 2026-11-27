from f1_core.teams import team_color
from f1_db.models import ConstructorStanding, Driver, DriverTeamStint, Season, Team
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.schemas.standings import DriverRef
from f1_api.schemas.teams import TeamProfile, TeamStandingPoint


class TeamService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def profile(self, ref: str) -> TeamProfile | None:
        t = (await self.session.execute(select(Team).where(Team.ref == ref))).scalar_one_or_none()
        if t is None:
            return None
        latest = (
            select(func.max(Season.year))
            .join(DriverTeamStint, DriverTeamStint.season_id == Season.id)
            .where(DriverTeamStint.team_id == t.id)
            .scalar_subquery()
        )
        drivers = (
            (
                await self.session.execute(
                    select(Driver)
                    .join(DriverTeamStint, DriverTeamStint.driver_id == Driver.id)
                    .join(Season, Season.id == DriverTeamStint.season_id)
                    .where(DriverTeamStint.team_id == t.id, Season.year == latest)
                    .distinct()
                    .order_by(Driver.family_name)
                )
            )
            .scalars()
            .all()
        )
        history = (
            await self.session.execute(
                select(Season.year, ConstructorStanding)
                .join(Season, Season.id == ConstructorStanding.season_id)
                .where(ConstructorStanding.team_id == t.id)
                .distinct(Season.year)
                .order_by(Season.year, ConstructorStanding.round.desc())
            )
        ).all()
        return TeamProfile(
            id=t.id,
            ref=t.ref,
            name=t.name,
            nationality=t.nationality,
            color=team_color(t.ref),
            drivers=[DriverRef.of(d) for d in drivers],
            standings_history=[
                TeamStandingPoint(
                    season=year,
                    round=c.round,
                    position=c.position,
                    points=float(c.points),
                    wins=c.wins,
                )
                for year, c in history
            ],
        )
