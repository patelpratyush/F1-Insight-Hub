from decimal import Decimal

import pytest
from f1_db.models import Driver, DriverStanding, Season, Team
from f1_db.session import make_engine, make_session_factory
from httpx import AsyncClient
from sqlalchemy import text


@pytest.fixture
async def seeded(pg_url: str) -> None:
    engine = make_engine(pg_url)
    async with make_session_factory(engine)() as s:
        await s.execute(text("truncate driver_standings, drivers, teams, seasons cascade"))
        season = Season(year=1999)
        team = Team(ref="mcl", name="McLaren", nationality="British")
        d1 = Driver(ref="nor", code="NOR", given_name="Lando", family_name="Norris", number=4)
        d2 = Driver(ref="pia", code="PIA", given_name="Oscar", family_name="Piastri", number=81)
        s.add_all([season, team, d1, d2])
        await s.flush()
        for rnd, pts_n, pts_p in [(1, "25", "18"), (2, "37.50", "43")]:
            s.add_all(
                [
                    DriverStanding(
                        season_id=season.id,
                        round=int(rnd),
                        driver_id=d1.id,
                        team_id=team.id,
                        position=1 if rnd == 1 else 2,
                        points=Decimal(pts_n),
                        wins=1,
                    ),
                    DriverStanding(
                        season_id=season.id,
                        round=int(rnd),
                        driver_id=d2.id,
                        team_id=team.id,
                        position=2 if rnd == 1 else 1,
                        points=Decimal(pts_p),
                        wins=0,
                    ),
                ]
            )
        await s.commit()
    await engine.dispose()


async def test_returns_latest_round_ordered_by_position(client: AsyncClient, seeded: None) -> None:
    resp = await client.get("/v1/standings/drivers", params={"season": 1999})
    assert resp.status_code == 200
    rows = resp.json()
    assert [r["driver"]["code"] for r in rows] == ["PIA", "NOR"]
    assert all(r["round"] == 2 for r in rows)


async def test_fractional_points_preserved(client: AsyncClient, seeded: None) -> None:
    rows = (await client.get("/v1/standings/drivers", params={"season": 1999})).json()
    nor = next(r for r in rows if r["driver"]["code"] == "NOR")
    assert nor["points"] == 37.5


async def test_empty_season_returns_empty_list(client: AsyncClient) -> None:
    resp = await client.get("/v1/standings/drivers", params={"season": 1998})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize("bad", ["abc", "1900", "3000", "-1", "2099"])
async def test_invalid_season_is_422_problem(client: AsyncClient, bad: str) -> None:
    resp = await client.get("/v1/standings/drivers", params={"season": bad})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")


async def test_default_season_falls_back_to_latest_with_data(
    client: AsyncClient, seeded: None
) -> None:
    resp = await client.get("/v1/standings/drivers")
    assert resp.status_code == 200
    rows = resp.json()
    assert [r["driver"]["code"] for r in rows] == ["PIA", "NOR"]
    assert all(r["season"] == 1999 for r in rows)


async def test_default_season_with_no_data_anywhere_is_empty(
    client: AsyncClient, pg_url: str
) -> None:
    engine = make_engine(pg_url)
    async with make_session_factory(engine)() as s:
        await s.execute(text("truncate driver_standings, drivers, teams, seasons cascade"))
        await s.commit()
    await engine.dispose()
    resp = await client.get("/v1/standings/drivers")
    assert resp.status_code == 200
    assert resp.json() == []
