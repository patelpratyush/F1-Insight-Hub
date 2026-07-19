from typing import Optional
from pydantic import BaseModel


class WeatherRequest(BaseModel):
    circuit_name: str


class RaceWeekendWeatherRequest(BaseModel):
    circuit_name: str
    race_date: Optional[str] = None
