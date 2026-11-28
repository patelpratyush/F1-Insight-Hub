"""OpenF1 (unofficial, community data) live feed, normalised to f1_core LiveEvents."""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from f1_core.live.events import Kind, LiveEvent

from f1_worker.resilience import CircuitBreaker

BASE = "https://api.openf1.org/v1"
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)  # ts for records without a date (sorts first)

# endpoint -> (event kind, date field used for the `after` cursor; None = no date filter)
ENDPOINTS: dict[str, tuple[Kind, str | None]] = {
    "position": ("position", "date"),
    "laps": ("lap", "date_start"),
    "intervals": ("interval", "date"),
    "stints": ("stint", None),
    "pit": ("pit", "date"),
    "race_control": ("flag", "date"),
    "weather": ("weather", "date"),
}

log = structlog.get_logger()


class OpenF1Unavailable(Exception):
    """Every endpoint failed: OpenF1 is down (distinct from an empty feed)."""


def _ms(seconds: Any) -> int | None:
    return None if seconds is None else round(float(seconds) * 1000)


def _gap(v: Any) -> str | None:
    # Strings such as "+1 LAP" are kept verbatim; numbers become "+12.346".
    if v is None or isinstance(v, str):
        return v
    return f"+{float(v):.3f}"


def _lap(r: dict[str, Any]) -> dict[str, object]:
    return {
        "lap_number": r.get("lap_number"),
        "lap_time_ms": _ms(r.get("lap_duration")),
        "sectors_ms": [_ms(r.get(f"duration_sector_{i}")) for i in (1, 2, 3)],
        "is_pit_out": bool(r.get("is_pit_out_lap")),
    }


def _stint(r: dict[str, Any]) -> dict[str, object]:
    age = r.get("tyre_age_at_start")
    if age is not None and r.get("lap_end") is not None and r.get("lap_start") is not None:
        age = int(age) + int(r["lap_end"]) - int(r["lap_start"])
    return {
        "compound": r.get("compound"),
        "tyre_age_laps": age,
        "stint_number": r.get("stint_number"),
    }


def _weather(r: dict[str, Any]) -> dict[str, object]:
    return {
        "air_temp_c": r.get("air_temperature"),
        "track_temp_c": r.get("track_temperature"),
        "humidity": r.get("humidity"),
        "rainfall": r.get("rainfall"),
        "wind_kph": None if r.get("wind_speed") is None else float(r["wind_speed"]) * 3.6,
    }


# Returns None to skip a record.
NORMALISE: dict[str, Callable[[dict[str, Any]], dict[str, object] | None]] = {
    "position": lambda r: {"position": r.get("position")},
    "laps": _lap,
    "intervals": lambda r: {
        "gap_to_leader": _gap(r.get("gap_to_leader")),
        "interval": _gap(r.get("interval")),
    },
    "stints": _stint,
    "pit": lambda r: {
        "in_pit": True,
        "lap_number": r.get("lap_number"),
        "duration_ms": _ms(r.get("pit_duration")),
    },
    # Session-wide flags only; driver-specific flags (blue flags etc.) are not the track state.
    # shortcut: retirements are not detected from race control yet; add when OUT is needed live.
    "race_control": lambda r: (
        {"flag": r["flag"]} if r.get("flag") and r.get("driver_number") is None else None
    ),
    "weather": _weather,
}


def _ts(raw: Any) -> datetime:
    if not raw:
        return EPOCH
    return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone(UTC)


class OpenF1Client:
    def __init__(
        self, client: httpx.AsyncClient | None = None, breaker: CircuitBreaker | None = None
    ) -> None:
        self.client = client or httpx.AsyncClient(timeout=5.0)
        self.breaker = breaker or CircuitBreaker(failure_threshold=5, reset_seconds=30)

    async def _get(self, url: str) -> list[dict[str, Any]]:
        async def go() -> list[dict[str, Any]]:
            resp = await self.client.get(url)
            if resp.status_code == 404:  # OpenF1 answers 404 for "no results"
                return []
            resp.raise_for_status()
            data: list[dict[str, Any]] = resp.json()
            return data

        return await self.breaker.call(go)

    async def events_since(
        self, session_key: int, after: Mapping[str, datetime] | None
    ) -> list[LiveEvent]:
        """New events across all endpoints, sorted by time, with seq=0 (the poller assigns
        seq). `after` maps event kind to the latest timestamp already seen for it."""
        after = after or {}
        events: list[LiveEvent] = []
        failures = 0
        for endpoint, (kind, date_field) in ENDPOINTS.items():
            url = f"{BASE}/{endpoint}?session_key={session_key}"
            if date_field and kind in after:
                stamp = after[kind].astimezone(UTC).replace(tzinfo=None).isoformat()
                url += f"&{date_field}>={stamp}"
            try:
                rows = await self._get(url)
            except Exception as exc:  # one bad endpoint must not stop the others
                failures += 1
                log.warning("openf1_endpoint_failed", endpoint=endpoint, error=str(exc))
                continue
            for r in rows:
                data = NORMALISE[endpoint](r)
                if data is None:
                    continue
                number = r.get("driver_number")
                events.append(
                    LiveEvent(
                        seq=0,
                        ts=_ts(r.get(date_field)) if date_field else EPOCH,
                        kind=kind,
                        driver_number=None if number is None else int(number),
                        data=data,
                    )
                )
        if failures == len(ENDPOINTS):
            raise OpenF1Unavailable(f"all {failures} OpenF1 endpoints failed")
        return sorted(events, key=lambda e: e.ts)

    async def records(self, endpoint: str, session_key: int) -> list[dict[str, Any]]:
        """Raw rows for one endpoint (used by the post-session flush)."""
        return await self._get(f"{BASE}/{endpoint}?session_key={session_key}")

    async def sessions(self, year: int) -> list[dict[str, Any]]:
        return await self._get(f"{BASE}/sessions?year={year}")
