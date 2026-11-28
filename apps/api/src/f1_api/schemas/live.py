from typing import Literal

from pydantic import BaseModel

SectorColor = Literal["purple", "green", "yellow", "none"]


class DriverTimingOut(BaseModel):
    number: int
    position: int | None
    code: str | None
    last_lap_ms: int | None
    best_lap_ms: int | None
    best_sectors_ms: tuple[int | None, int | None, int | None]
    gap_to_leader: str | None  # verbatim from OpenF1, e.g. "+1 LAP"
    interval: str | None
    compound: str | None
    tyre_age_laps: int | None
    in_pit: bool
    retired: bool
    sectors: tuple[SectorColor, SectorColor, SectorColor]


class LiveStateOut(BaseModel):
    """Unofficial, community data (OpenF1). `drivers` is in timing-tower order."""

    drivers: list[DriverTimingOut]
    flag: str
    lap: int | None
    session_best_lap_ms: int | None
    session_best_sectors_ms: tuple[int | None, int | None, int | None]
    last_seq: int
    status: Literal["waiting", "live", "finished"]
