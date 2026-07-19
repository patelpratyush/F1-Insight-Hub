"""
Prediction service — ties together ratings engine + Monte Carlo simulator.
Runs CPU-bound simulation in thread pool to avoid blocking the event loop.
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..core.backtest import rating_concordance
from ..core.f1_ratings import compute_driver_scores_with_breakdown
from ..core.monte_carlo import simulate_race
from ..models.predict import (
    DriverPrediction, ModelInfo, PositionRange, RaceGridEntry, RatingBreakdown,
)

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mc_")
_SIMULATION_TRIALS = 1000


def _confidence_from_range(p10: int, p90: int, grid_size: int) -> float:
    """Tighter Monte Carlo spread relative to grid size -> higher confidence."""
    if grid_size <= 1:
        return 1.0
    spread = (p90 - p10) / grid_size
    return round(max(0.0, min(1.0, 1 - spread)), 4)


class PredictionService:
    def __init__(self, cache):
        self._cache = cache

    def _current_year(self, year: Optional[int] = None) -> int:
        return year or datetime.now(timezone.utc).year

    async def run_simulation(
        self, track: str, weather: str, year: Optional[int],
    ) -> tuple[List[RaceGridEntry], Dict[str, Dict], ModelInfo]:
        y = self._current_year(year)
        cache = self._cache

        await cache.ensure_year(y)

        code_to_name = cache.get_driver_code_map(y)
        driver_standings = cache.get_driver_standings_map(y)
        constructor_standings = cache.get_constructor_standings_map(y)

        if not code_to_name:
            code_to_name = _fallback_driver_map()

        loop = asyncio.get_event_loop()
        breakdowns = await loop.run_in_executor(
            _executor,
            compute_driver_scores_with_breakdown,
            code_to_name, driver_standings, constructor_standings, track, weather,
        )
        scores = {code: b["score"] for code, b in breakdowns.items()}
        results = await loop.run_in_executor(
            _executor, simulate_race, scores, _SIMULATION_TRIALS,
        )

        team_map = {s["driver"]: s["team"] for s in cache.get_driver_standings(y)}
        grid_size = len(results)

        grid = [
            RaceGridEntry(
                position=r["predicted_position"],
                driver=r["driver"],
                name=code_to_name.get(r["driver"], r["driver"]),
                team=team_map.get(r["driver"], "Unknown"),
                win_probability=r["win_pct"],
                podium_probability=r["podium_pct"],
                expected_points=r["expected_pts"],
                position_range=PositionRange(
                    p10=r["p10_pos"], p90=r["p90_pos"], std_dev=r["pos_std"],
                ),
                confidence=_confidence_from_range(r["p10_pos"], r["p90_pos"], grid_size),
            )
            for r in results
        ]

        concordance = rating_concordance(scores, driver_standings)
        model_info = ModelInfo(
            simulation_trials=_SIMULATION_TRIALS,
            concordant_pct=concordance["concordant_pct"],
            compared_pairs=concordance["compared_pairs"],
        )

        return grid, breakdowns, model_info

    async def predict_race_grid(
        self, track: str, weather: str = "dry", year: Optional[int] = None
    ) -> List[RaceGridEntry]:
        grid, _, _ = await self.run_simulation(track, weather, year)
        return grid

    async def predict_driver(
        self, driver_code: str, track: str, weather: str = "dry", year: Optional[int] = None
    ) -> Optional[DriverPrediction]:
        grid, breakdowns, model_info = await self.run_simulation(track, weather, year)
        entry = next((e for e in grid if e.driver == driver_code), None)
        if not entry:
            return None

        key_factors = _build_key_factors(driver_code, weather, entry)
        breakdown = breakdowns.get(driver_code, {})
        rating_breakdown = RatingBreakdown(
            base_skill=breakdown.get("base_skill", 0),
            team_mult=breakdown.get("team_mult", 0),
            form_factor=breakdown.get("form_factor", 0),
            weather_mod=breakdown.get("weather_mod", 0),
            track_mod=breakdown.get("track_mod", 0),
        ) if breakdown else None

        return DriverPrediction(
            driver=driver_code,
            name=entry.name,
            team=entry.team,
            predicted_position=entry.position,
            win_probability=entry.win_probability,
            podium_probability=entry.podium_probability,
            expected_points=entry.expected_points,
            key_factors=key_factors,
            position_range=entry.position_range,
            confidence=entry.confidence,
            rating_breakdown=rating_breakdown,
            model_info=model_info,
        )


def _build_key_factors(code: str, weather: str, entry: RaceGridEntry) -> List[str]:
    factors = []
    if entry.win_probability > 0.3:
        factors.append("High win probability based on current championship form")
    if weather.lower() in ("wet", "rain", "heavy rain"):
        factors.append("Wet conditions add variability — wet-weather skill is a differentiator")
    if entry.position <= 3:
        factors.append("Strong team performance and car pace")
    if entry.position > 10:
        factors.append("Midfield battle — strategy and reliability key")
    return factors or ["Competitive midfield — any result possible"]


def _fallback_driver_map() -> Dict[str, str]:
    import json, os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "fallback_driver_roster.json")
    try:
        with open(path) as f:
            data = json.load(f)
        return {code: d["name"] for code, d in data.get("drivers", {}).items()}
    except Exception:
        return {}
