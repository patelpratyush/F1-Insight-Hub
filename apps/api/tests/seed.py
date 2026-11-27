"""Shared seed for the Phase 1 read API tests (season 1997)."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from f1_db.models import (
    Circuit,
    ConstructorStanding,
    Driver,
    DriverStanding,
    DriverTeamStint,
    Race,
    RaceSession,
    Season,
    SessionResult,
    Team,
    WeatherSample,
)
from f1_db.session import make_engine, make_session_factory
from sqlalchemy import text

YEAR = 1997


@dataclass(frozen=True)
class SeedIds:
    year: int


def _at(day: int, hour: int) -> datetime:
    return datetime(YEAR, 3, day, hour, tzinfo=UTC)


async def seed_season(pg_url: str) -> SeedIds:
    engine = make_engine(pg_url)
    async with make_session_factory(engine)() as s:
        await s.execute(text("truncate seasons, circuits, drivers, teams cascade"))
        season = Season(year=YEAR)
        ca = Circuit(ref="ring_a", name="Ring A", locality="A", country="X", lat=1.0, lon=2.0)
        cb = Circuit(ref="ring_b", name="Ring B", locality="B", country="Y", lat=3.0, lon=4.0)
        alpha = Team(ref="alpha", name="Alpha", nationality="X")
        beta = Team(ref="beta", name="Beta", nationality="Y")
        steady = Driver(ref="steady", code="STE", given_name="Sam", family_name="Steady", number=1)
        swapper = Driver(ref="swapper", code="SWA", given_name="Sid", family_name="Swap", number=2)
        dnfer = Driver(ref="dnfer", code="DNF", given_name="Dan", family_name="Fail", number=3)
        s.add_all([season, ca, cb, alpha, beta, steady, swapper, dnfer])
        await s.flush()

        races = [
            Race(
                season_id=season.id,
                round=1,
                name="GP One",
                circuit_name="Ring A",
                race_date=date(YEAR, 3, 2),
                circuit_id=ca.id,
            ),
            Race(
                season_id=season.id,
                round=2,
                name="GP Two",
                circuit_name="Ring B",
                race_date=date(YEAR, 3, 9),
                circuit_id=cb.id,
            ),
            Race(
                season_id=season.id,
                round=3,
                name="GP Three",
                circuit_name="Ring A",
                race_date=date(YEAR, 3, 16),
                circuit_id=ca.id,
            ),
        ]
        s.add_all(races)
        await s.flush()
        r1, r2, r3 = races

        def sess(
            race: Race, type_: str, day: int, hour: int, status: str = "finished"
        ) -> RaceSession:
            return RaceSession(race_id=race.id, type=type_, starts_at=_at(day, hour), status=status)

        s.add_all(
            [
                sess(r1, "Q", 1, 14),
                sess(r1, "R", 2, 14),
                sess(r2, "SQ", 7, 10),
                sess(r2, "SPRINT", 8, 10),
                sess(r2, "Q", 8, 14),
                sess(r2, "R", 9, 14),
                sess(r3, "Q", 15, 14, "cancelled"),
                sess(r3, "R", 16, 14, "scheduled"),
            ]
        )

        def res(
            race: Race,
            st: str,
            d: Driver,
            t: Team,
            pos: int | None,
            pts: str,
            status: str = "Finished",
            grid: int | None = None,
        ) -> SessionResult:
            return SessionResult(
                race_id=race.id,
                session_type=st,
                driver_id=d.id,
                team_id=t.id,
                position=pos,
                grid=grid,
                status=status,
                points=Decimal(pts),
                time_ms=None if pos is None else 5_400_000 + (pos * 1000),
            )

        s.add_all(
            [
                res(r1, "R", steady, alpha, 1, "25", grid=2),
                res(r1, "R", swapper, alpha, 2, "18", grid=1),
                res(r1, "R", dnfer, beta, None, "0", status="Retired", grid=3),
                res(r1, "Q", steady, alpha, 1, "0"),
                res(r2, "R", swapper, beta, 1, "25"),
                res(r2, "R", steady, alpha, 2, "18"),
                res(r2, "R", dnfer, beta, 3, "15"),
                res(r2, "SPRINT", swapper, beta, 1, "8"),
            ]
        )
        s.add_all(
            [
                DriverTeamStint(
                    season_id=season.id,
                    driver_id=steady.id,
                    team_id=alpha.id,
                    from_round=1,
                    to_round=None,
                ),
                DriverTeamStint(
                    season_id=season.id,
                    driver_id=swapper.id,
                    team_id=alpha.id,
                    from_round=1,
                    to_round=1,
                ),
                DriverTeamStint(
                    season_id=season.id,
                    driver_id=swapper.id,
                    team_id=beta.id,
                    from_round=2,
                    to_round=None,
                ),
                DriverTeamStint(
                    season_id=season.id,
                    driver_id=dnfer.id,
                    team_id=beta.id,
                    from_round=1,
                    to_round=None,
                ),
            ]
        )
        for rnd, a_pts, b_pts in [(1, "43", "0"), (2, "61", "48")]:
            s.add_all(
                [
                    ConstructorStanding(
                        season_id=season.id,
                        round=rnd,
                        team_id=alpha.id,
                        position=1,
                        points=Decimal(a_pts),
                        wins=1,
                    ),
                    ConstructorStanding(
                        season_id=season.id,
                        round=rnd,
                        team_id=beta.id,
                        position=2,
                        points=Decimal(b_pts),
                        wins=rnd - 1,
                    ),
                ]
            )
        s.add_all(
            [
                DriverStanding(
                    season_id=season.id,
                    round=2,
                    driver_id=swapper.id,
                    team_id=beta.id,
                    position=1,
                    points=Decimal("51"),
                    wins=1,
                ),
                DriverStanding(
                    season_id=season.id,
                    round=2,
                    driver_id=steady.id,
                    team_id=alpha.id,
                    position=2,
                    points=Decimal("43"),
                    wins=1,
                ),
            ]
        )
        s.add_all(
            [
                WeatherSample(
                    race_id=r1.id,
                    observed_at=_at(2, 12),
                    air_temp_c=21.5,
                    humidity=50.0,
                    wind_kph=10.0,
                    rain_probability=None,
                    source="open-meteo",
                ),
                WeatherSample(
                    race_id=r1.id,
                    observed_at=_at(2, 13),
                    air_temp_c=22.0,
                    humidity=48.0,
                    wind_kph=12.0,
                    rain_probability=10.0,
                    source="open-meteo",
                ),
            ]
        )
        await s.commit()
    await engine.dispose()
    return SeedIds(year=YEAR)
