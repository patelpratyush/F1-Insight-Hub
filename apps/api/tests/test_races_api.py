import pytest
from httpx import AsyncClient
from seed import YEAR, SeedIds, seed_season


@pytest.fixture
async def seeded(pg_url: str) -> SeedIds:
    return await seed_season(pg_url)


async def test_race_detail_404_problem(client: AsyncClient, seeded: SeedIds) -> None:
    r = await client.get(f"/v1/races/{YEAR}/99")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")


async def test_dnf_row_has_null_position_and_status(client: AsyncClient, seeded: SeedIds) -> None:
    body = (await client.get(f"/v1/races/{YEAR}/1")).json()
    dnf = next(r for r in body["results"]["R"] if r["driver"]["ref"] == "dnfer")
    assert dnf["position"] is None and dnf["status"] == "Retired" and dnf["time_ms"] is None
    assert [r["position"] for r in body["results"]["R"]] == [1, 2, None]


async def test_results_attribute_team_per_round(client: AsyncClient, seeded: SeedIds) -> None:
    r1 = (await client.get(f"/v1/races/{YEAR}/1")).json()
    r2 = (await client.get(f"/v1/races/{YEAR}/2")).json()
    team = {
        n: next(r["team"]["name"] for r in b["results"]["R"] if r["driver"]["ref"] == "swapper")
        for n, b in ((1, r1), (2, r2))
    }
    assert team == {1: "Alpha", 2: "Beta"}


async def test_race_without_sprint_has_empty_sprint_results(
    client: AsyncClient, seeded: SeedIds
) -> None:
    body = (await client.get(f"/v1/races/{YEAR}/1")).json()
    assert body["results"]["SPRINT"] == [] and len(body["results"]["Q"]) == 1
    assert len(body["weather"]) == 2 and body["weather"][0]["rain_probability"] is None


async def test_race_with_cancelled_session_and_no_results(
    client: AsyncClient, seeded: SeedIds
) -> None:
    body = (await client.get(f"/v1/races/{YEAR}/3")).json()
    assert body["results"] == {"R": [], "Q": [], "SPRINT": []}
    assert body["weather"] == []
    assert {s["type"]: s["status"] for s in body["sessions"]}["Q"] == "cancelled"
