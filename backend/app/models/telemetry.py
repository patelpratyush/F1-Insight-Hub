from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class TelemetryRequest(BaseModel):
    year: int
    race: str
    session: str = "R"      # R | Q | FP1 | FP2 | FP3 | S
    driver: str             # driver code


class DriverComparisonRequest(BaseModel):
    year: int
    race: str
    session: str = "Q"
    driver1: str
    driver2: str


class SpeedTraceRequest(BaseModel):
    year: int
    race: str
    session: str = "Q"
    driver: str
    lap: Optional[int] = None   # None = fastest


class TrackMapRequest(BaseModel):
    year: int
    race: str
    session: str = "Q"
    driver: str
    lap: Optional[int] = None


class WeatherContextRequest(BaseModel):
    year: int
    race: str
    session: str = "R"
