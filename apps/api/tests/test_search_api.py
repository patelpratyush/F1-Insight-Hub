from datetime import date

import pytest
from f1_db.models import Driver, Race, Season, Team
from f1_db.session import make_engine, make_session_factory
from httpx import AsyncClient
from sqlalchemy import text


@pytest.fixture
async def seeded(pg_url: str) -> None:
    engine = make_engine(pg_url)
    async with make_session_factory(engine)() as s:
        await s.execute(text("truncate seasons, circuits, drivers, teams cascade"))
        season = Season(year=1997)
        s.add_all(
            [
                season,
                Driver(ref="perez", code="PER", given_name="Sergio", family_name="Pérez"),
                Driver(
                    ref="max_verstappen", code="VER", given_name="Max", family_name="Verstappen"
                ),
                Driver(ref="bearman", code="BEA", given_name="Oliver", family_name="Bearman"),
                Team(ref="red_bull", name="Red Bull"),
                Team(ref="ferrari", name="Ferrari"),
            ]
        )
        await s.flush()
        s.add(
            Race(
                season_id=season.id,
                round=4,
                name="Emilia Romagna Grand Prix",
                circuit_name="Imola",
                race_date=date(1997, 4, 27),
            )
        )
        await s.commit()
    await engine.dispose()


async def test_finds_driver_ignoring_case_and_accents(client: AsyncClient, seeded: None) -> None:
    hits = (await client.get("/v1/search", params={"q": "PEREZ"})).json()
    assert hits[0]["kind"] == "driver" and hits[0]["href"] == "/drivers/perez"
    assert hits[0]["label"] == "Sergio Pérez"


async def test_prefix_ranks_before_substring(client: AsyncClient, seeded: None) -> None:
    hits = (await client.get("/v1/search", params={"q": "ver"})).json()
    assert [h["href"] for h in hits] == ["/drivers/max_verstappen", "/drivers/bearman"]


async def test_finds_teams_and_races(client: AsyncClient, seeded: None) -> None:
    team = (await client.get("/v1/search", params={"q": "red"})).json()
    assert {"kind": "team", "href": "/teams/red_bull"}.items() <= team[0].items()
    race = (await client.get("/v1/search", params={"q": "romagna"})).json()
    assert race[0]["kind"] == "race" and race[0]["href"] == "/races/1997/4"
    assert race[0]["hint"] == "1997"


@pytest.mark.parametrize("q", ["", "a", "x" * 65])
async def test_bad_query_length_is_422(client: AsyncClient, q: str) -> None:
    resp = await client.get("/v1/search", params={"q": q})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")


@pytest.mark.parametrize("q", ["%%", "__", "\\\\"])
async def test_wildcards_are_escaped(client: AsyncClient, seeded: None, q: str) -> None:
    hits = (await client.get("/v1/search", params={"q": q})).json()
    assert hits == []


async def test_results_capped_at_20(client: AsyncClient, pg_url: str, seeded: None) -> None:
    engine = make_engine(pg_url)
    async with make_session_factory(engine)() as s:
        s.add_all(
            Driver(ref=f"smith{i}", given_name="Ann", family_name=f"Smith{i:02d}")
            for i in range(25)
        )
        await s.commit()
    await engine.dispose()
    hits = (await client.get("/v1/search", params={"q": "smith"})).json()
    assert len(hits) == 20 and hits[0]["label"] == "Ann Smith00"
