from collections.abc import Mapping
from dataclasses import replace
from typing import cast

from f1_core.live.events import LiveEvent
from f1_core.live.state import (
    DriverTiming,
    SectorColor,
    Sectors,
    SectorTimes,
    SessionStatus,
    TimingState,
)


def _opt_int(v: object) -> int | None:
    return None if v is None else int(cast(int, v))


def _opt_str(v: object) -> str | None:
    return None if v is None else str(v)


def _best(a: int | None, b: int | None) -> int | None:
    if a is None:
        return b
    return a if b is None else min(a, b)


def _color(value: int | None, personal: int | None, overall: int | None) -> SectorColor:
    if value is None:
        return "none"
    if overall is not None and value <= overall:
        return "purple"
    if personal is not None and value <= personal:
        return "green"
    return "yellow"


def _apply_lap(
    state: TimingState, d: DriverTiming, data: Mapping[str, object]
) -> tuple[TimingState, DriverTiming]:
    lap_ms = _opt_int(data.get("lap_time_ms"))
    raw = cast(list[object], data.get("sectors_ms") or [None, None, None])
    secs = [_opt_int(v) for v in raw[:3]]
    # Overall bests include this lap (so a new session best is purple); personal bests are
    # compared before this lap counts (so a personal improvement is green).
    overall = [_best(o, v) for o, v in zip(state.session_best_sectors_ms, secs, strict=True)]
    colors = cast(
        Sectors,
        tuple(_color(v, p, o) for v, p, o in zip(secs, d.best_sectors_ms, overall, strict=True)),
    )
    personal = cast(
        SectorTimes, tuple(_best(p, v) for p, v in zip(d.best_sectors_ms, secs, strict=True))
    )
    d2 = replace(
        d,
        last_lap_ms=lap_ms if lap_ms is not None else d.last_lap_ms,
        best_lap_ms=_best(d.best_lap_ms, lap_ms),
        best_sectors_ms=personal,
        sectors=colors,
    )
    s2 = replace(
        state,
        session_best_lap_ms=_best(state.session_best_lap_ms, lap_ms),
        session_best_sectors_ms=cast(SectorTimes, tuple(overall)),
    )
    return s2, d2


def apply_event(state: TimingState, event: LiveEvent) -> TimingState:
    """Pure: returns a new state. Events at or below last_seq are ignored (resume dedupe)."""
    if event.seq <= state.last_seq:
        return state
    state = replace(state, last_seq=event.seq)
    data = event.data
    if event.driver_number is None:
        if event.kind == "flag":
            return replace(state, flag=str(data["flag"]))
        if event.kind == "status" and "session" in data:
            return replace(state, status=cast(SessionStatus, data["session"]))
        if event.kind == "status" and "lap" in data:
            return replace(state, lap=_opt_int(data["lap"]))
        return state  # session-level weather etc. only advances last_seq
    drivers = dict(state.drivers)
    d = drivers.get(event.driver_number) or DriverTiming(number=event.driver_number)
    if event.kind == "position":
        d = replace(d, position=_opt_int(data["position"]))
    elif event.kind == "interval":
        d = replace(
            d,
            gap_to_leader=_opt_str(data.get("gap_to_leader")),
            interval=_opt_str(data.get("interval")),
        )
    elif event.kind == "stint":
        d = replace(
            d,
            compound=_opt_str(data.get("compound")),
            tyre_age_laps=_opt_int(data.get("tyre_age_laps")),
        )
    elif event.kind == "pit":
        d = replace(d, in_pit=bool(data["in_pit"]))
    elif event.kind == "status":
        d = replace(d, retired=bool(data.get("retired", d.retired)))
    elif event.kind == "lap":
        state, d = _apply_lap(state, d, data)
    drivers[event.driver_number] = d
    return replace(state, drivers=drivers)


def ordered_tower(state: TimingState) -> list[DriverTiming]:
    """By position; drivers without one after (by number); retired drivers last."""

    def key(d: DriverTiming) -> tuple[int, int, int]:
        return (1 if d.retired else 0, d.position if d.position is not None else 10_000, d.number)

    return sorted(state.drivers.values(), key=key)
