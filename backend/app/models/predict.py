from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class DriverPredictRequest(BaseModel):
    driver: str = Field(..., min_length=2, max_length=10, description="3-letter driver code, e.g. VER")
    track: str = Field(..., min_length=1, max_length=100, description="Race name, e.g. 'Monaco Grand Prix'")
    weather: Literal["dry", "wet", "mixed"] = Field(default="dry", description="dry | wet | mixed")
    year: Optional[int] = Field(default=None, ge=1950, le=2100)


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
    track: str = Field(..., min_length=1, max_length=100)
    weather: Literal["dry", "wet", "mixed"] = "dry"
    year: Optional[int] = Field(default=None, ge=1950, le=2100)


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
