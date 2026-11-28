import pytest
from httpx import AsyncClient
from seed import YEAR, SeedIds, seed_season


@pytest.fixture
async def seeded(pg_url: str) -> SeedIds:
    return await seed_season(pg_url)


async def test_team_profile_includes_color_and_drivers(
    client: AsyncClient, seeded: SeedIds
) -> None:
    body = (await client.get("/v1/teams/beta")).json()
    assert body["color"] == "#E10600"
    assert sorted(d["ref"] for d in body["drivers"]) == ["dnfer", "swapper"]
    assert [(h["round"], h["points"]) for h in body["standings_history"]] == [(2, 48.0)]


async def test_unknown_team_is_404(client: AsyncClient, seeded: SeedIds) -> None:
    assert (await client.get("/v1/teams/nobody")).status_code == 404


async def test_constructor_standings_latest_round(client: AsyncClient, seeded: SeedIds) -> None:
    rows = (await client.get("/v1/standings/constructors", params={"season": YEAR})).json()
    assert [(r["team"]["ref"], r["position"], r["points"], r["round"]) for r in rows] == [
        ("alpha", 1, 61.0, 2),
        ("beta", 2, 48.0, 2),
    ]
