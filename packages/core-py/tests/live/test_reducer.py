from datetime import UTC, datetime

from f1_core.live.events import LiveEvent
from f1_core.live.reducer import apply_event, ordered_tower
from f1_core.live.state import TimingState

T0 = datetime(2025, 3, 16, 4, 0, tzinfo=UTC)


def ev(seq: int, kind: str, number: int | None = None, **data: object) -> LiveEvent:
    return LiveEvent(seq=seq, ts=T0, kind=kind, driver_number=number, data=data)  # type: ignore[arg-type]


def test_position_events_order_the_tower() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "position", 4, position=2))
    s = apply_event(s, ev(2, "position", 1, position=1))
    assert [d.number for d in ordered_tower(s)] == [1, 4]


def test_stale_or_duplicate_seq_is_ignored() -> None:
    s = apply_event(TimingState.empty(), ev(5, "position", 1, position=1))
    again = apply_event(s, ev(5, "position", 1, position=9))
    older = apply_event(s, ev(3, "position", 1, position=9))
    assert again.drivers[1].position == 1 and older.drivers[1].position == 1
    assert again.last_seq == 5


def test_overall_best_lap_is_purple_and_personal_best_green() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "lap", 1, lap_time_ms=90000, sectors_ms=[30000, 30000, 30000]))
    s = apply_event(s, ev(2, "lap", 4, lap_time_ms=91000, sectors_ms=[30500, 30500, 30000]))
    assert s.drivers[1].sectors == ("purple", "purple", "purple")
    assert s.drivers[4].sectors == ("yellow", "yellow", "purple")
    s = apply_event(s, ev(3, "lap", 4, lap_time_ms=90500, sectors_ms=[30200, 30200, 30100]))
    assert s.drivers[4].best_lap_ms == 90500
    assert s.drivers[4].sectors == ("green", "green", "yellow")
    assert s.session_best_lap_ms == 90000


def test_gap_strings_are_kept_verbatim() -> None:
    s = apply_event(
        TimingState.empty(), ev(1, "interval", 7, gap_to_leader="+1 LAP", interval=None)
    )
    assert s.drivers[7].gap_to_leader == "+1 LAP"
    assert s.drivers[7].interval is None


def test_numeric_gaps_become_strings_without_nan() -> None:
    s = apply_event(TimingState.empty(), ev(1, "interval", 7, gap_to_leader=1.234, interval=0.5))
    assert (s.drivers[7].gap_to_leader, s.drivers[7].interval) == ("1.234", "0.5")


def test_retired_driver_sorts_last_and_pit_flag_toggles() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "position", 1, position=1))
    s = apply_event(s, ev(2, "position", 2, position=2))
    s = apply_event(s, ev(3, "position", 3, position=3))
    s = apply_event(s, ev(4, "status", 1, retired=True))
    s = apply_event(s, ev(5, "pit", 2, in_pit=True))
    assert [d.number for d in ordered_tower(s)] == [2, 3, 1]
    assert s.drivers[2].in_pit is True
    s = apply_event(s, ev(6, "pit", 2, in_pit=False))
    assert s.drivers[2].in_pit is False


def test_drivers_without_position_sort_after_positioned_by_number() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "stint", 44, compound="SOFT", tyre_age_laps=3))
    s = apply_event(s, ev(2, "stint", 16, compound="HARD", tyre_age_laps=0))
    s = apply_event(s, ev(3, "position", 81, position=1))
    assert [d.number for d in ordered_tower(s)] == [81, 16, 44]
    assert (s.drivers[44].compound, s.drivers[44].tyre_age_laps) == ("SOFT", 3)


def test_flag_and_status_events() -> None:
    s = apply_event(TimingState.empty(), ev(1, "flag", None, flag="YELLOW"))
    assert s.flag == "YELLOW"
    s = apply_event(s, ev(2, "status", None, session="live"))
    assert s.status == "live"
    s = apply_event(s, ev(3, "status", None, lap=12))
    assert s.lap == 12
    s = apply_event(s, ev(4, "weather", None, air_temp_c=20.0))
    assert s.last_seq == 4


def test_unknown_driver_in_lap_event_creates_driver() -> None:
    s = apply_event(
        TimingState.empty(), ev(1, "lap", 99, lap_time_ms=95000, sectors_ms=[None, None, None])
    )
    assert 99 in s.drivers and s.drivers[99].last_lap_ms == 95000
    assert s.drivers[99].sectors == ("none", "none", "none")


def test_reducer_is_pure() -> None:
    s = TimingState.empty()
    apply_event(s, ev(1, "position", 1, position=1))
    assert s.drivers == {}
    assert s.last_seq == 0
