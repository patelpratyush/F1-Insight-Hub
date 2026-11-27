from f1_db.models import Driver, DriverStanding, DriverTeamStint, Race, Season, SessionResult, Team
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.schemas.drivers import DriverProfile, DriverSeason, TeamStintOut
from f1_api.services.races import result_rows_stmt, to_row

RECENT = 10


class DriverService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def profile(self, ref: str) -> DriverProfile | None:
        d = (
            await self.session.execute(select(Driver).where(Driver.ref == ref))
        ).scalar_one_or_none()
        if d is None:
            return None
        # Final standing per season: latest round (DISTINCT ON season).
        seasons = (
            await self.session.execute(
                select(Season.year, Team.name, DriverStanding)
                .join(Season, Season.id == DriverStanding.season_id)
                .join(Team, Team.id == DriverStanding.team_id)
                .where(DriverStanding.driver_id == d.id)
                .distinct(Season.year)
                .order_by(Season.year, DriverStanding.round.desc())
            )
        ).all()
        recent = (
            await self.session.execute(
                result_rows_stmt(SessionResult.driver_id == d.id, SessionResult.session_type == "R")
                .join(Race, Race.id == SessionResult.race_id)
                .order_by(Race.race_date.desc())
                .limit(RECENT)
            )
        ).all()
        stints = (
            await self.session.execute(
                select(Team.name, Season.year, DriverTeamStint)
                .join(Team, Team.id == DriverTeamStint.team_id)
                .join(Season, Season.id == DriverTeamStint.season_id)
                .where(DriverTeamStint.driver_id == d.id)
                .order_by(Season.year, DriverTeamStint.from_round)
            )
        ).all()
        return DriverProfile(
            id=d.id,
            ref=d.ref,
            code=d.code,
            given_name=d.given_name,
            family_name=d.family_name,
            number=d.number,
            nationality=d.nationality,
            seasons=[
                DriverSeason(
                    year=year, team=team, position=s.position, points=float(s.points), wins=s.wins
                )
                for year, team, s in seasons
            ],
            recent_results=[to_row(r, dr, t) for r, dr, t in recent],
            team_history=[
                TeamStintOut(team=team, season=year, from_round=st.from_round, to_round=st.to_round)
                for team, year, st in stints
            ],
        )
