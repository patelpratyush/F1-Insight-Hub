from datetime import UTC, datetime

import httpx
import pytest
import respx
from f1_worker.sources.openf1 import ENDPOINTS, OpenF1Client, OpenF1Unavailable

BASE = "https://api.openf1.org/v1"


def _empty_except(**bodies: list[dict[str, object]]) -> None:
    for ep in ENDPOINTS:
        respx.get(url__startswith=f"{BASE}/{ep}?").mock(
            return_value=httpx.Response(200, json=bodies.get(ep, []))
        )


@respx.mock
async def test_normalises_position_and_interval_events() -> None:
    _empty_except(
        position=[{"driver_number": 1, "position": 1, "date": "2025-03-16T04:05:00+00:00"}],
        intervals=[
            {
                "driver_number": 4,
                "gap_to_leader": "+1 LAP",
                "interval": None,
                "date": "2025-03-16T04:05:01+00:00",
            },
            {
                "driver_number": 16,
                "gap_to_leader": 12.3456,
                "interval": 0.5,
                "date": "2025-03-16T04:05:02+00:00",
            },
        ],
    )
    events = await OpenF1Client().events_since(9158, None)
    assert {e.kind for e in events} == {"position", "interval"}
    lapped = next(e for e in events if e.driver_number == 4)
    assert lapped.data == {"gap_to_leader": "+1 LAP", "interval": None}
    close = next(e for e in events if e.driver_number == 16)
    assert close.data == {"gap_to_leader": "+12.346", "interval": "+0.500"}
    assert [e.ts for e in events] == sorted(e.ts for e in events)


@respx.mock
async def test_normalises_laps_stints_pit_flags_and_weather() -> None:
    _empty_except(
        laps=[
            {
                "driver_number": 1,
                "lap_number": 3,
                "lap_duration": 91.234,
                "duration_sector_1": 30.1,
                "duration_sector_2": None,
                "duration_sector_3": 31.0,
                "is_pit_out_lap": False,
                "date_start": "2025-03-16T04:03:00+00:00",
            }
        ],
        stints=[
            {
                "driver_number": 1,
                "stint_number": 2,
                "compound": "HARD",
                "lap_start": 20,
                "lap_end": 25,
                "tyre_age_at_start": 3,
            }
        ],
        pit=[
            {
                "driver_number": 1,
                "lap_number": 19,
                "pit_duration": 22.5,
                "date": "2025-03-16T04:04:00+00:00",
            }
        ],
        race_control=[
            {"flag": "YELLOW", "driver_number": None, "date": "2025-03-16T04:04:30+00:00"},
            {"flag": "BLUE", "driver_number": 4, "date": "2025-03-16T04:04:31+00:00"},
            {"flag": None, "message": "TRACK LIMITS", "date": "2025-03-16T04:04:32+00:00"},
        ],
        weather=[
            {
                "air_temperature": 21.5,
                "track_temperature": 35.0,
                "humidity": 50,
                "rainfall": 0,
                "wind_speed": 3.2,
                "date": "2025-03-16T04:04:40+00:00",
            }
        ],
    )
    by_kind = {e.kind: e for e in await OpenF1Client().events_since(9158, None)}
    assert set(by_kind) == {"lap", "stint", "pit", "flag", "weather"}
    assert by_kind["lap"].data == {
        "lap_number": 3,
        "lap_time_ms": 91234,
        "sectors_ms": [30100, None, 31000],
        "is_pit_out": False,
    }
    assert by_kind["stint"].data == {"compound": "HARD", "tyre_age_laps": 8, "stint_number": 2}
    assert by_kind["pit"].data == {"in_pit": True, "lap_number": 19, "duration_ms": 22500}
    assert by_kind["flag"].data == {"flag": "YELLOW"} and by_kind["flag"].driver_number is None
    assert by_kind["weather"].data["track_temp_c"] == 35.0


@respx.mock
async def test_after_cursor_is_sent_per_endpoint() -> None:
    _empty_except()
    after = {"position": datetime(2025, 3, 16, 4, 5, tzinfo=UTC)}
    await OpenF1Client().events_since(9158, after)
    sent = {c.request.url.path.rsplit("/", 1)[1]: str(c.request.url) for c in respx.calls}
    assert (
        "date%3E=2025-03-16T04:05:00" in sent["position"]
        or "date>=2025-03-16T04:05:00" in sent["position"]
    )
    assert ">" not in sent["laps"] and "%3E" not in sent["laps"]


@respx.mock
async def test_empty_feed_returns_no_events() -> None:
    _empty_except()
    assert await OpenF1Client().events_since(9158, None) == []


@respx.mock
async def test_http_404_for_unknown_session_returns_empty_and_no_crash() -> None:
    respx.get(url__startswith=BASE).mock(
        return_value=httpx.Response(404, json={"detail": "No results found."})
    )
    assert await OpenF1Client().events_since(1, None) == []


@respx.mock
async def test_one_failing_endpoint_is_skipped() -> None:
    _empty_except(position=[{"driver_number": 1, "position": 1, "date": "2025-03-16T04:05:00Z"}])
    respx.get(url__startswith=f"{BASE}/laps?").mock(return_value=httpx.Response(500))
    events = await OpenF1Client().events_since(9158, None)
    assert [e.kind for e in events] == ["position"]


@respx.mock
async def test_all_endpoints_failing_raises_unavailable() -> None:
    respx.get(url__startswith=BASE).mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(OpenF1Unavailable):
        await OpenF1Client().events_since(9158, None)
