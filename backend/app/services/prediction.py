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

from ..core.f1_ratings import compute_driver_scores
from ..core.monte_carlo import simulate_race
from ..models.predict import DriverPrediction, RaceGridEntry

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mc_")


class PredictionService:
    def __init__(self, cache):
        self._cache = cache

    def _current_year(self, year: Optional[int] = None) -> int:
        return year or datetime.now(timezone.utc).year

    async def predict_race_grid(
        self, track: str, weather: str = "dry", year: Optional[int] = None
    ) -> List[RaceGridEntry]:
        y = self._current_year(year)
        cache = self._cache

        await cache.ensure_year(y)

        code_to_name = cache.get_driver_code_map(y)
        driver_standings = cache.get_driver_standings_map(y)
        constructor_standings = cache.get_constructor_standings_map(y)

        if not code_to_name:
            code_to_name = _fallback_driver_map()

        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            _executor,
            compute_driver_scores,
            code_to_name, driver_standings, constructor_standings, track, weather,
        )
        results = await loop.run_in_executor(
            _executor, simulate_race, scores, 1000,
        )

        name_map = code_to_name
        team_map = {s["driver"]: s["team"] for s in cache.get_driver_standings(y)}

        return [
            RaceGridEntry(
                position=r["predicted_position"],
                driver=r["driver"],
                name=name_map.get(r["driver"], r["driver"]),
                team=team_map.get(r["driver"], "Unknown"),
                win_probability=r["win_pct"],
                podium_probability=r["podium_pct"],
                expected_points=r["expected_pts"],
            )
            for r in results
        ]

    async def predict_driver(
        self, driver_code: str, track: str, weather: str = "dry", year: Optional[int] = None
    ) -> Optional[DriverPrediction]:
        grid = await self.predict_race_grid(track, weather, year)
        y = self._current_year(year)
        name_map = self._cache.get_driver_code_map(y)
        team_map = {s["driver"]: s["team"] for s in self._cache.get_driver_standings(y)}

        entry = next((e for e in grid if e.driver == driver_code), None)
        if not entry:
            return None

        key_factors = _build_key_factors(driver_code, weather, entry)
        return DriverPrediction(
            driver=driver_code,
            name=name_map.get(driver_code, driver_code),
            team=team_map.get(driver_code, "Unknown"),
            predicted_position=entry.position,
            win_probability=entry.win_probability,
            podium_probability=entry.podium_probability,
            expected_points=entry.expected_points,
            key_factors=key_factors,
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
