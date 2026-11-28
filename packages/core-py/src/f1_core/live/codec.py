"""JSON form of TimingState shared by the worker (Redis), the api and the browser.
`drivers` is serialised as a list already in timing-tower order."""

import json
from dataclasses import asdict
from typing import Any, cast

from f1_core.live.reducer import ordered_tower
from f1_core.live.state import DriverTiming, Sectors, SectorTimes, SessionStatus, TimingState


def state_dict(state: TimingState) -> dict[str, Any]:
    body = asdict(state)
    body["drivers"] = [asdict(d) for d in ordered_tower(state)]
    return body


def dump_state(state: TimingState) -> str:
    return json.dumps(state_dict(state), separators=(",", ":"))


def _driver(d: dict[str, Any]) -> DriverTiming:
    return DriverTiming(
        **{
            **d,
            "best_sectors_ms": cast(SectorTimes, tuple(d["best_sectors_ms"])),
            "sectors": cast(Sectors, tuple(d["sectors"])),
        }
    )


def load_state(raw: str | bytes) -> TimingState:
    body = json.loads(raw)
    return TimingState(
        drivers={d["number"]: _driver(d) for d in body["drivers"]},
        flag=body["flag"],
        lap=body["lap"],
        session_best_lap_ms=body["session_best_lap_ms"],
        session_best_sectors_ms=cast(SectorTimes, tuple(body["session_best_sectors_ms"])),
        last_seq=body["last_seq"],
        status=cast(SessionStatus, body["status"]),
    )
