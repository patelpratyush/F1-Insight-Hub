from pydantic import BaseModel, Field
from typing import List, Optional


class DriverPredictRequest(BaseModel):
    driver: str = Field(..., description="3-letter driver code, e.g. VER")
    track: str = Field(..., description="Race name, e.g. 'Monaco Grand Prix'")
    weather: str = Field(default="dry", description="dry | wet | mixed")
    year: Optional[int] = None


class DriverPrediction(BaseModel):
    driver: str
    name: str
    team: str
    predicted_position: int
    win_probability: float
    podium_probability: float
    expected_points: float
    key_factors: List[str]


class RacePredictRequest(BaseModel):
    track: str
    weather: str = "dry"
    year: Optional[int] = None


class RaceGridEntry(BaseModel):
    position: int
    driver: str
    name: str
    team: str
    win_probability: float
    podium_probability: float
    expected_points: float


class RaceGridPrediction(BaseModel):
    track: str
    weather: str
    year: int
    grid: List[RaceGridEntry]
