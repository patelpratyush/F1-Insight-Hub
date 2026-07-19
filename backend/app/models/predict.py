from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional


class DriverPredictRequest(BaseModel):
    driver: str = Field(..., min_length=2, max_length=10, description="3-letter driver code, e.g. VER")
    track: str = Field(..., min_length=1, max_length=100, description="Race name, e.g. 'Monaco Grand Prix'")
    weather: Literal["dry", "wet", "mixed"] = Field(default="dry", description="dry | wet | mixed")
    year: Optional[int] = Field(default=None, ge=1950, le=2100)


class PositionRange(BaseModel):
    p10: int
    p90: int
    std_dev: float


class RatingBreakdown(BaseModel):
    base_skill: float
    team_mult: float
    form_factor: float
    weather_mod: float
    track_mod: float


class ModelInfo(BaseModel):
    method: str = "Rating-based Monte Carlo simulation"
    simulation_trials: int
    concordant_pct: Optional[float] = None
    compared_pairs: int = 0


class DriverPrediction(BaseModel):
    driver: str
    name: str
    team: str
    predicted_position: int
    win_probability: float
    podium_probability: float
    expected_points: float
    key_factors: List[str]
    position_range: Optional[PositionRange] = None
    confidence: Optional[float] = None
    rating_breakdown: Optional[RatingBreakdown] = None
    model_info: Optional[ModelInfo] = None


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
    position_range: Optional[PositionRange] = None
    confidence: Optional[float] = None


class RaceGridPrediction(BaseModel):
    track: str
    weather: str
    year: int
    grid: List[RaceGridEntry]
    model_info: Optional[ModelInfo] = None
