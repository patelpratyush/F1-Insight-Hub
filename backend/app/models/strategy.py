from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class StrategyRequest(BaseModel):
    driver: str
    track: str
    laps: int = Field(default=57, ge=10, le=78)
    starting_tire: str = "MEDIUM"  # SOFT | MEDIUM | HARD
    weather: str = "dry"
    year: Optional[int] = None
    stint_compounds: Optional[List[str]] = None  # explicit user-picked stint plan, overrides auto-derivation


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
    stint_number: int
    tire_compound: str
    start_lap: int
    end_lap: int
    laps: int
    avg_lap_time: float
    degradation_level: str


class PitStop(BaseModel):
    lap: int
    stint_number: int
    old_tire: str
    new_tire: str
    pit_time: float
    reason: str


class TimelineEntry(BaseModel):
    lap_start: int
    lap_end: int
    tire: str
    cumulative_time: float


class OptimizationMetrics(BaseModel):
    consistency: float  # 0-1, higher = more even lap times across stints
    baseline_time: float


class RiskAnalysis(BaseModel):
    overall_risk: float  # 0-1, higher = riskier strategy
    pit_stop_risk: float
    weather_risk: float


class StrategyResult(BaseModel):
    strategy_id: str
    driver: str
    track: str
    total_time: float
    total_race_time: str  # formatted H:MM:SS.mmm
    total_seconds: float
    pit_stops: List[PitStop]
    stints: List[StintResult]
    predicted_position: int
    efficiency_score: float
    confidence: float
    timeline: List[TimelineEntry]
    optimization_metrics: OptimizationMetrics
    risk_analysis: RiskAnalysis
    summary: str
