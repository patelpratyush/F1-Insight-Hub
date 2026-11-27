import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import respx
from f1_worker.sources.jolpica import JolpicaClient

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "driver_standings_2025.json").read_text()
)
URL = "https://api.jolpi.ca/ergast/f1/2025/driverStandings.json"


@respx.mock
async def test_parses_standings_with_fractional_points() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    rows = await JolpicaClient().driver_standings(2025)
    assert len(rows) == 2
    assert rows[0].driver_ref == "norris"
    assert rows[0].points == Decimal("423.5")
    assert rows[0].team_ref == "mclaren"
    assert rows[0].round == 24


@respx.mock
async def test_empty_standings_list_returns_empty() -> None:
    empty = {"MRData": {"StandingsTable": {"season": "2030", "StandingsLists": []}}}
    respx.get("https://api.jolpi.ca/ergast/f1/2030/driverStandings.json").mock(
        return_value=httpx.Response(200, json=empty)
    )
    assert await JolpicaClient().driver_standings(2030) == []


@respx.mock
async def test_retries_429_then_succeeds() -> None:
    route = respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json=FIXTURE),
        ]
    )
    rows = await JolpicaClient(retry_wait=0).driver_standings(2025)
    assert route.call_count == 2 and len(rows) == 2


@respx.mock
async def test_persistent_500_raises_after_three_attempts() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await JolpicaClient(retry_wait=0).driver_standings(2025)
    assert route.call_count == 3


@respx.mock
async def test_backoff_is_exponential_and_honours_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("f1_worker.sources.jolpica.asyncio.sleep", fake_sleep)
    respx.get(URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await JolpicaClient(retry_wait=0.5).driver_standings(2025)
    assert sleeps == [0.5, 1.0]

    sleeps.clear()
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(200, json=FIXTURE),
        ]
    )
    await JolpicaClient(retry_wait=0.5).driver_standings(2025)
    assert sleeps == [2.0]
