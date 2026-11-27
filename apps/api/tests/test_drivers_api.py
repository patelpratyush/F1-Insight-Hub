import pytest
from httpx import AsyncClient
from seed import YEAR, SeedIds, seed_season


@pytest.fixture
async def seeded(pg_url: str) -> SeedIds:
    return await seed_season(pg_url)


async def test_driver_profile_has_team_history_in_order(
    client: AsyncClient, seeded: SeedIds
) -> None:
    body = (await client.get("/v1/drivers/swapper")).json()
    assert [(h["team"], h["from_round"], h["to_round"]) for h in body["team_history"]] == [
        ("Alpha", 1, 1),
        ("Beta", 2, None),
    ]
    assert body["seasons"] == [
        {"year": YEAR, "team": "Beta", "position": 1, "points": 51.0, "wins": 1}
    ]


async def test_recent_results_newest_first_with_team_per_round(
    client: AsyncClient, seeded: SeedIds
) -> None:
    body = (await client.get("/v1/drivers/swapper")).json()
    assert [(r["position"], r["team"]["name"]) for r in body["recent_results"]] == [
        (1, "Beta"),
        (2, "Alpha"),
    ]


async def test_unknown_driver_is_404(client: AsyncClient, seeded: SeedIds) -> None:
    r = await client.get("/v1/drivers/nobody")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
