from datetime import datetime

from pydantic import BaseModel

from f1_api.schemas.calendar import RaceSummary
from f1_api.schemas.standings import DriverRef, TeamRef


class WeatherOut(BaseModel):
    observed_at: datetime
    air_temp_c: float | None
    track_temp_c: float | None
    humidity: float | None
    wind_kph: float | None
    rain_probability: float | None
    source: str


class ResultRow(BaseModel):
    position: int | None
    grid: int | None
    status: str
    points: float
    time_ms: int | None
    driver: DriverRef
    team: TeamRef


class RaceDetail(RaceSummary):
    weather: list[WeatherOut]
    results: dict[str, list[ResultRow]]  # keys: R, Q, SPRINT (always present)
