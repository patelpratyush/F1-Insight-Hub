from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SectorColor = Literal["purple", "green", "yellow", "none"]
Sectors = tuple[SectorColor, SectorColor, SectorColor]
SectorTimes = tuple[int | None, int | None, int | None]
NONE3: Sectors = ("none", "none", "none")
SessionStatus = Literal["waiting", "live", "finished"]


@dataclass(frozen=True)
class DriverTiming:
    number: int
    position: int | None = None
    code: str | None = None
    last_lap_ms: int | None = None
    best_lap_ms: int | None = None
    best_sectors_ms: SectorTimes = (None, None, None)
    gap_to_leader: str | None = None  # verbatim, e.g. "+1 LAP"; never parsed to a number
    interval: str | None = None
    compound: str | None = None
    tyre_age_laps: int | None = None
    in_pit: bool = False
    retired: bool = False
    sectors: Sectors = NONE3


@dataclass(frozen=True)
class TimingState:
    drivers: dict[int, DriverTiming] = field(default_factory=dict)
    flag: str = "GREEN"
    lap: int | None = None
    session_best_lap_ms: int | None = None
    session_best_sectors_ms: SectorTimes = (None, None, None)
    last_seq: int = 0
    status: SessionStatus = "waiting"

    @staticmethod
    def empty() -> TimingState:
        return TimingState()
