import pytest
from httpx import AsyncClient
from seed import YEAR, SeedIds, seed_season


@pytest.fixture
async def seeded(pg_url: str) -> SeedIds:
    return await seed_season(pg_url)


async def test_calendar_lists_races_in_round_order(client: AsyncClient, seeded: SeedIds) -> None:
    rows = (await client.get("/v1/calendar", params={"season": YEAR})).json()
    assert [r["round"] for r in rows] == [1, 2, 3]
    assert rows[0]["circuit"]["ref"] == "ring_a" and rows[0]["season"] == YEAR


async def test_sprint_weekend_has_sprint_session_and_cancelled_is_reported(
    client: AsyncClient, seeded: SeedIds
) -> None:
    rows = (await client.get("/v1/calendar", params={"season": YEAR})).json()
    assert "SPRINT" in {s["type"] for s in rows[1]["sessions"]}
    assert "SPRINT" not in {s["type"] for s in rows[0]["sessions"]}
    q = next(s for s in rows[2]["sessions"] if s["type"] == "Q")
    assert q["status"] == "cancelled"


async def test_session_times_are_utc(client: AsyncClient, seeded: SeedIds) -> None:
    rows = (await client.get("/v1/calendar", params={"season": YEAR})).json()
    starts = rows[0]["sessions"][0]["starts_at"]
    assert starts.endswith(("Z", "+00:00"))


async def test_etag_returns_304_on_match(client: AsyncClient, seeded: SeedIds) -> None:
    first = await client.get("/v1/calendar", params={"season": YEAR})
    assert first.headers["cache-control"] == "public, max-age=60, stale-while-revalidate=300"
    assert first.headers["etag"].startswith('W/"')
    second = await client.get(
        "/v1/calendar", params={"season": YEAR}, headers={"If-None-Match": first.headers["etag"]}
    )
    assert second.status_code == 304 and second.content == b""


async def test_far_future_season_is_422(client: AsyncClient, seeded: SeedIds) -> None:
    assert (await client.get("/v1/calendar", params={"season": 2099})).status_code == 422


async def test_unknown_season_is_empty_list(client: AsyncClient, seeded: SeedIds) -> None:
    resp = await client.get("/v1/calendar", params={"season": 1960})
    assert resp.status_code == 200 and resp.json() == []
