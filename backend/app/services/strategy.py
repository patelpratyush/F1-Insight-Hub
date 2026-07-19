"""
F1 Strategy simulation service.
Ported from strategy_simulation_service.py — same degradation model,
cleaner async interface, optional Gemini AI optimize.
"""
import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="strategy_")

TIRE_COMPOUNDS = {
    "SOFT":   {"base_delta": 0.0,  "deg_rate": 0.12, "peak_laps": 15},
    "MEDIUM": {"base_delta": 0.5,  "deg_rate": 0.07, "peak_laps": 25},
    "HARD":   {"base_delta": 1.0,  "deg_rate": 0.04, "peak_laps": 35},
    "INTER":  {"base_delta": -2.0, "deg_rate": 0.06, "peak_laps": 25},
    "WET":    {"base_delta": -5.0, "deg_rate": 0.05, "peak_laps": 30},
}

BASE_LAP_TIME = 90.0  # seconds — track-specific override via track_chars
PIT_LOSS      = 22.0  # seconds per pit stop


def _tire_lap_time(compound: str, lap_in_stint: int) -> float:
    t = TIRE_COMPOUNDS.get(compound, TIRE_COMPOUNDS["MEDIUM"])
    deg = t["deg_rate"] * max(0, lap_in_stint - t["peak_laps"])
    return BASE_LAP_TIME + t["base_delta"] + deg


def _format_race_time(total_seconds: float) -> str:
    hours, rem = divmod(total_seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{int(hours)}:{int(minutes):02d}:{secs:06.3f}"


def _weather_risk(weather: str) -> float:
    w = weather.lower()
    if w in ("wet", "heavy rain"):
        return 0.6
    if w in ("mixed", "variable", "light rain"):
        return 0.3
    return 0.05


def _simulate_strategy(
    driver: str, track: str, laps: int,
    stint_compounds: List[str], weather: str,
) -> Dict:
    stints = []
    timeline = []
    total_time = 0.0
    lap = 1
    for i, compound in enumerate(stint_compounds):
        is_last = i == len(stint_compounds) - 1
        stint_laps = laps // len(stint_compounds)
        if is_last:
            stint_laps = laps - (len(stint_compounds) - 1) * (laps // len(stint_compounds))

        stint_time = 0.0
        for lap_in_stint in range(1, stint_laps + 1):
            stint_time += _tire_lap_time(compound, lap_in_stint)

        if not is_last:
            stint_time += PIT_LOSS  # pit stop loss at end of stint

        avg = stint_time / stint_laps
        deg_level = "Low" if avg < BASE_LAP_TIME + 1 else "Medium" if avg < BASE_LAP_TIME + 2 else "High"

        stints.append({
            "stint_number": i + 1,
            "tire_compound": compound,
            "start_lap": lap,
            "end_lap": lap + stint_laps - 1,
            "laps": stint_laps,
            "avg_lap_time": round(avg, 3),
            "degradation_level": deg_level,
        })
        total_time += stint_time
        timeline.append({
            "lap_start": lap,
            "lap_end": lap + stint_laps - 1,
            "tire": compound,
            "cumulative_time": round(total_time, 2),
        })
        lap += stint_laps

    pit_stop_count = len(stint_compounds) - 1
    pos_estimate = max(1, min(20, 8 - pit_stop_count + int(total_time % 3)))

    pit_stops = [
        {
            "lap": stints[i]["end_lap"],
            "stint_number": stints[i]["stint_number"],
            "old_tire": stints[i]["tire_compound"],
            "new_tire": stints[i + 1]["tire_compound"],
            "pit_time": PIT_LOSS,
            "reason": f"Scheduled stop — {stints[i]['degradation_level'].lower()} degradation on {stints[i]['tire_compound']}",
        }
        for i in range(len(stints) - 1)
    ]

    # Efficiency: how close total_time is to a zero-degradation baseline
    # run on the fastest compound with the same number of stops.
    baseline_time = BASE_LAP_TIME * laps + PIT_LOSS * pit_stop_count
    efficiency_score = round(min(100.0, (baseline_time / total_time) * 100), 1)

    # Confidence: tighter spread of stint pace -> more predictable strategy.
    stint_avgs = [s["avg_lap_time"] for s in stints]
    pace_std = float(np.std(stint_avgs)) if len(stint_avgs) > 1 else 0.0
    confidence = round(max(0.0, min(1.0, 1 - pace_std / BASE_LAP_TIME)), 4)

    pit_stop_risk = round(min(1.0, pit_stop_count * 0.15), 4)
    weather_risk = _weather_risk(weather)

    return {
        "strategy_id": str(uuid.uuid4())[:8],
        "driver": driver,
        "track": track,
        "total_time": round(total_time, 2),
        "total_seconds": round(total_time, 2),
        "total_race_time": _format_race_time(total_time),
        "pit_stops": pit_stops,
        "stints": stints,
        "predicted_position": pos_estimate,
        "efficiency_score": efficiency_score,
        "confidence": confidence,
        "timeline": timeline,
        "optimization_metrics": {
            "consistency": confidence,
            "baseline_time": round(baseline_time, 2),
        },
        "risk_analysis": {
            "overall_risk": round((pit_stop_risk + weather_risk) / 2, 4),
            "pit_stop_risk": pit_stop_risk,
            "weather_risk": weather_risk,
        },
        "summary": f"{pit_stop_count}-stop {'-'.join(stint_compounds)} strategy",
    }


class StrategyService:
    async def simulate(
        self, driver: str, track: str, laps: int,
        starting_tire: str, weather: str,
        stint_compounds: Optional[List[str]] = None,
    ) -> Dict:
        compounds = stint_compounds or _choose_compounds(starting_tire, laps, weather)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, _simulate_strategy, driver, track, laps, compounds, weather
        )

    async def compare(
        self, driver: str, track: str, laps: int,
        strategies: List[List[str]], weather: str,
    ) -> List[Dict]:
        loop = asyncio.get_event_loop()
        results = list(await asyncio.gather(*[
            loop.run_in_executor(_executor, _simulate_strategy, driver, track, laps, s, weather)
            for s in strategies
        ]))
        results.sort(key=lambda x: x["total_time"])
        return results

    async def optimize(
        self, driver: str, track: str, laps: int,
        weather: str, use_ai: bool = False,
    ) -> Dict:
        candidates = [
            ["SOFT", "HARD"],
            ["MEDIUM", "MEDIUM"],
            ["SOFT", "MEDIUM", "HARD"],
            ["MEDIUM", "HARD"],
            ["SOFT", "SOFT", "HARD"],
        ]
        loop = asyncio.get_event_loop()
        results = list(await asyncio.gather(*[
            loop.run_in_executor(_executor, _simulate_strategy, driver, track, laps, s, weather)
            for s in candidates
        ]))
        results.sort(key=lambda x: x["total_time"])
        best = results[0]

        if use_ai:
            ai_insight = await _gemini_insight(best, results[:3], driver, track, weather)
            best["ai_insight"] = ai_insight

        return {"optimal": best, "alternatives": results[1:3]}

    def get_tire_compounds(self, track: str) -> Dict:
        return {
            compound: {
                "base_delta_s": data["base_delta"],
                "degradation_rate": data["deg_rate"],
                "peak_laps": data["peak_laps"],
            }
            for compound, data in TIRE_COMPOUNDS.items()
        }

    def get_available_tracks(self) -> List[str]:
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "track_characteristics.json")
        try:
            with open(path) as f:
                return list(json.load(f).keys())
        except Exception:
            return []


def _choose_compounds(starting: str, laps: int, weather: str) -> List[str]:
    if weather.lower() in ("wet", "heavy rain"):
        return ["WET", "WET"] if laps > 40 else ["WET"]
    if laps <= 30:
        return [starting, "HARD"]
    return [starting, "MEDIUM", "HARD"] if laps > 55 else [starting, "HARD"]


async def _gemini_insight(best: Dict, top3: List[Dict], driver: str, track: str, weather: str) -> str:
    try:
        import os
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            return "AI insights unavailable (no API key configured)"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"F1 strategy for {driver} at {track} ({weather} conditions).\n"
            f"Best strategy: {best['summary']} ({best['total_time']}s total).\n"
            f"Alternatives: {[s['summary'] for s in top3[1:]]}.\n"
            "Give a 2-sentence strategic recommendation."
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        logger.warning(f"Gemini insight failed: {e}")
        return "AI insight unavailable"
