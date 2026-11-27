from decimal import Decimal

from f1_db.models import Driver, DriverStanding, Season, Team
from f1_db.session import make_session_factory
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

EXPECTED = {
    "seasons",
    "teams",
    "drivers",
    "races",
    "driver_standings",
    "session_results",
    "ingestion_runs",
    "alembic_version",
}


async def test_baseline_creates_expected_tables(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert names >= EXPECTED


async def test_auth_schema_exists(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        row = await conn.execute(
            text("select 1 from information_schema.schemata where schema_name = 'auth'")
        )
    assert row.scalar() == 1


async def test_fractional_points_round_trip(engine: AsyncEngine) -> None:
    factory = make_session_factory(engine)
    async with factory() as s:
        season = Season(year=2099)
        team = Team(ref="t-frac", name="T", nationality=None)
        driver = Driver(ref="d-frac", code="FRC", given_name="A", family_name="B")
        s.add_all([season, team, driver])
        await s.flush()
        s.add(
            DriverStanding(
                season_id=season.id,
                round=1,
                driver_id=driver.id,
                team_id=team.id,
                position=1,
                points=Decimal("12.50"),
                wins=0,
            )
        )
        await s.commit()
        got = (await s.execute(text("select points from driver_standings"))).scalar_one()
    assert got == Decimal("12.50")
