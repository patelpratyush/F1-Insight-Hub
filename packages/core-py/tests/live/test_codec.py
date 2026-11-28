import json
from datetime import UTC, datetime

from f1_core.live.codec import dump_state, load_state
from f1_core.live.events import LiveEvent
from f1_core.live.reducer import apply_event
from f1_core.live.state import TimingState

T0 = datetime(2025, 3, 16, 4, 0, tzinfo=UTC)


def ev(seq: int, kind: str, number: int | None = None, **data: object) -> LiveEvent:
    return LiveEvent(seq=seq, ts=T0, kind=kind, driver_number=number, data=data)  # type: ignore[arg-type]


def test_round_trip_and_drivers_in_tower_order() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "position", 4, position=2))
    s = apply_event(s, ev(2, "position", 1, position=1))
    s = apply_event(s, ev(3, "lap", 1, lap_time_ms=90000, sectors_ms=[30000, None, 30000]))
    s = apply_event(s, ev(4, "status", None, session="live"))
    raw = dump_state(s)
    body = json.loads(raw)
    assert [d["number"] for d in body["drivers"]] == [1, 4]
    assert body["status"] == "live" and body["last_seq"] == 4
    assert load_state(raw) == s


def test_empty_state_round_trips() -> None:
    assert load_state(dump_state(TimingState.empty())) == TimingState.empty()
