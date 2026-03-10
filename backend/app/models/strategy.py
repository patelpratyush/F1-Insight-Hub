from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class StrategyRequest(BaseModel):
    driver: str
    track: str
    laps: int = Field(default=57, ge=10, le=78)
    starting_tire: str = "MEDIUM"  # SOFT | MEDIUM | HARD
    weather: str = "dry"
    year: Optional[int] = None


class StrategyCompareRequest(BaseModel):
    driver: str
    track: str
    laps: int = 57
    strategies: List[List[str]]   # e.g. [["SOFT","HARD"], ["MEDIUM","MEDIUM"]]
    weather: str = "dry"


class StrategyOptimizeRequest(BaseModel):
    driver: str
    track: str
    laps: int = 57
    weather: str = "dry"
    use_ai: bool = False


class StintResult(BaseModel):
    stint: int
    tire: str
    start_lap: int
    end_lap: int
    laps: int
    avg_lap_time: float
    degradation: str


class StrategyResult(BaseModel):
    strategy_id: str
    driver: str
    track: str
    total_time: float
    pit_stops: int
    stints: List[StintResult]
    final_position_estimate: int
    summary: str
