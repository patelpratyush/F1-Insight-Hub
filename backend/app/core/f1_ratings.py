"""
Dynamic F1 driver and team ratings engine.
Combines JSON config ratings with live Jolpica standings data.
"""
import json
import logging
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config")

# Weights for the form_factor calculation from standings points
_MAX_EXPECTED_POINTS = 200.0   # rough upper bound mid-season
_WEATHER_PROFILES: Dict[str, Dict[str, float]] = {
    # driver_name -> {dry, wet}  (override table for known wet-weather specialists)
    "Max Verstappen":    {"dry": 1.00, "wet": 1.05},
    "Lewis Hamilton":    {"dry": 0.97, "wet": 1.06},
    "George Russell":    {"dry": 0.95, "wet": 1.02},
    "Fernando Alonso":   {"dry": 0.93, "wet": 1.04},
    "Lando Norris":      {"dry": 0.98, "wet": 1.01},
    "Pierre Gasly":      {"dry": 0.88, "wet": 1.00},
}
_DEFAULT_WEATHER = {"dry": 1.0, "wet": 0.95}


def _load_json(filename: str) -> Dict:
    path = os.path.join(CONFIG_DIR, filename)
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {filename}: {e}")
        return {}


def _load_driver_ratings() -> Dict[str, Dict]:
    data = _load_json("fallback_driver_ratings.json")
    return data.get("drivers", {})


def _load_team_ratings() -> Dict[str, Dict]:
    data = _load_json("fallback_team_ratings.json")
    return data.get("teams", {})


def _load_track_characteristics() -> Dict[str, Dict]:
    return _load_json("track_characteristics.json")


def _find_team_rating(team_name: str, team_ratings: Dict[str, Dict]) -> Dict:
    """Fuzzy match team name against ratings keys."""
    default = {"dry_pace": 0.70, "wet_pace": 0.70, "strategy": 0.70, "reliability": 0.75}
    if team_name in team_ratings:
        return team_ratings[team_name]
    # partial match
    for key, val in team_ratings.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return val
    return default


def compute_driver_scores(
    driver_code_to_name: Dict[str, str],
    driver_standings: Dict[str, Dict],   # {code: {points, position, team, wins}}
    constructor_standings: Dict[str, Dict],  # {team_name: {points, position}}
    track_name: str = "",
    weather: str = "dry",                 # "dry" | "wet" | "mixed"
) -> Dict[str, float]:
    """
    Return {driver_code: score} where score is a 0–1 float
    representing overall predicted performance strength.

    Formula:
      score = base_skill × team_mult × form_factor × weather_mod
    """
    dr_ratings = _load_driver_ratings()
    team_ratings = _load_team_ratings()
    track_chars = _load_track_characteristics()

    is_wet = weather.lower() in ("wet", "heavy rain", "light rain", "rain")
    is_mixed = weather.lower() in ("mixed", "variable")

    # Normalise constructor points to 0–1
    max_constructor_pts = max(
        (s.get("points", 0) for s in constructor_standings.values()), default=1
    ) or 1
    max_driver_pts = max(
        (s.get("points", 0) for s in driver_standings.values()), default=1
    ) or 1

    scores: Dict[str, float] = {}

    for code, name in driver_code_to_name.items():
        # Base skill from config (default 0.70)
        dr_cfg = dr_ratings.get(name, {})
        if is_wet:
            base = dr_cfg.get("wet_skill", dr_cfg.get("overall_skill", 0.70))
        else:
            base = dr_cfg.get("overall_skill", 0.70)

        # Team performance multiplier from constructor standings
        standing = driver_standings.get(code, {})
        team = standing.get("team", "Unknown")
        con_standing = constructor_standings.get(team, {})
        con_pts = con_standing.get("points", 0)
        team_mult = 0.8 + 0.2 * (con_pts / max_constructor_pts)  # 0.8–1.0 range

        # Form factor from driver standings points (0.85–1.0 range)
        dr_pts = standing.get("points", 0)
        form = 0.85 + 0.15 * (dr_pts / max_driver_pts)

        # Weather modifier
        weather_profile = _WEATHER_PROFILES.get(name, _DEFAULT_WEATHER)
        if is_wet:
            weather_mod = weather_profile["wet"]
        elif is_mixed:
            weather_mod = (weather_profile["dry"] + weather_profile["wet"]) / 2
        else:
            weather_mod = weather_profile["dry"]

        # Track affinity (optional — track_chars may define per-driver affinities)
        track_mod = 1.0
        if track_name and track_name in track_chars:
            affinity = track_chars[track_name].get("driver_affinity", {})
            track_mod = affinity.get(code, affinity.get(name, 1.0))

        score = base * team_mult * form * weather_mod * track_mod
        scores[code] = min(score, 1.0)

    return scores
