"""
Data-driven F1 ratings engine.

Driver ratings: 2025 teammate-normalized (grid delta + race delta).
Team ratings:   2026 recency-weighted (grid + race + positions gained + reliability).
Blending:       confidence = n_2026_races / (n_2026_races + PRIOR_VIRTUAL_RACES)

Called synchronously from CacheService.initialize() and _periodic_refresh().
Writes output to config/computed_ratings.json.
"""
import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

logger = logging.getLogger(__name__)

CONFIG_DIR            = os.path.join(os.path.dirname(__file__), "..", "..", "config")
COMPUTED_RATINGS_PATH = os.path.join(CONFIG_DIR, "computed_ratings.json")

SCALE_MIN         = 0.60
SCALE_MAX_DRIVER  = 0.98
SCALE_MAX_TEAM    = 0.97
PRIOR_VIRTUAL_RACES = 4   # prior counts as this many virtual races of evidence


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _normalize_dict(values: Dict[str, float], lo: float, hi: float) -> Dict[str, float]:
    """
    Linearly scale values to [lo, hi].
    If all values are equal, map everyone to the midpoint.
    """
    if not values:
        return {}
    mn, mx = min(values.values()), max(values.values())
    if mx == mn:
        mid = round((lo + hi) / 2, 4)
        return {k: mid for k in values}
    return {
        k: round(lo + (v - mn) / (mx - mn) * (hi - lo), 4)
        for k, v in values.items()
    }


# ── Driver ratings ────────────────────────────────────────────────────────────

def compute_driver_ratings(results: List[Dict]) -> Dict[str, Dict]:
    """
    Compute driver skill ratings from race results using teammate normalization.

    For each race where a team has exactly 2 drivers:
      grid_delta  = teammate_grid   - driver_grid    (+ = driver qualified ahead)
      race_delta  = teammate_finish - driver_finish   (+ = driver finished ahead)

    Grid deltas excluded when either driver has grid == 0 (pit lane start).
    Race deltas excluded when either driver did not finish (status != "Finished").
    """
    driver_data: Dict[str, Dict] = defaultdict(
        lambda: {"grid_deltas": [], "race_deltas": [], "team": ""}
    )

    for race in results:
        # Group drivers by team for this race
        teams: Dict[str, List[Dict]] = defaultdict(list)
        for r in race.get("results", []):
            if r.get("team"):
                teams[r["team"]].append(r)

        for team_name, drivers in teams.items():
            if len(drivers) != 2:
                continue

            d1, d2 = drivers[0], drivers[1]
            n1, n2 = d1["name"], d2["name"]
            driver_data[n1]["team"] = team_name
            driver_data[n2]["team"] = team_name

            # Grid delta — exclude pit lane starts (grid == 0)
            g1, g2 = d1.get("grid", 0), d2.get("grid", 0)
            if g1 > 0 and g2 > 0:
                driver_data[n1]["grid_deltas"].append(g2 - g1)
                driver_data[n2]["grid_deltas"].append(g1 - g2)

            # Race delta — only when both classified "Finished"
            if d1.get("status") == "Finished" and d2.get("status") == "Finished":
                p1, p2 = d1.get("position", 20), d2.get("position", 20)
                driver_data[n1]["race_deltas"].append(p2 - p1)
                driver_data[n2]["race_deltas"].append(p1 - p2)

    if not driver_data:
        return {}

    # Raw average deltas per driver
    raw: Dict[str, Dict] = {
        name: {
            "grid": _mean(data["grid_deltas"]),
            "race": _mean(data["race_deltas"]),
        }
        for name, data in driver_data.items()
    }

    grid_norm = _normalize_dict({n: v["grid"] for n, v in raw.items()}, SCALE_MIN, SCALE_MAX_DRIVER)
    race_norm = _normalize_dict({n: v["race"] for n, v in raw.items()}, SCALE_MIN, SCALE_MAX_DRIVER)

    ratings: Dict[str, Dict] = {}
    for name in raw:
        overall    = round(0.5 * grid_norm[name] + 0.5 * race_norm[name], 4)
        overall    = min(max(overall, SCALE_MIN), SCALE_MAX_DRIVER)
        race_craft = round(min(max(race_norm[name], SCALE_MIN), SCALE_MAX_DRIVER), 4)
        ratings[name] = {
            "overall_skill":      overall,
            "wet_skill":          round(overall * 0.97, 4),   # placeholder — no wet detection yet
            "race_craft":         race_craft,
            "strategy_execution": round((overall + race_craft) / 2, 4),
        }

    return ratings


# ── Team ratings ──────────────────────────────────────────────────────────────

def compute_team_ratings(results: List[Dict]) -> Dict[str, Dict]:
    """
    Compute team performance ratings from race results.

    Metrics per race (recency-weighted):
      grid_perf       = mean finishing position of team's drivers
      race_perf       = mean finishing position of team's drivers
      positions_gained = mean (grid - finish) across team's drivers
      reliability     = fraction of team's drivers that finished

    Returns dict of team_name -> rating dict.
    """
    team_data: Dict[str, Dict] = defaultdict(
        lambda: {
            "grid_positions": [],
            "finish_positions": [],
            "positions_gained": [],
            "finishes": [],
            "entries": [],
        }
    )

    for race in results:
        teams: Dict[str, List[Dict]] = defaultdict(list)
        for r in race.get("results", []):
            if r.get("team"):
                teams[r["team"]].append(r)

        for team_name, drivers in teams.items():
            for d in drivers:
                grid = d.get("grid", 0)
                pos  = d.get("position", 20)
                finished = d.get("status") == "Finished"
                team_data[team_name]["entries"].append(1)
                team_data[team_name]["finish_positions"].append(pos)
                team_data[team_name]["finishes"].append(1 if finished else 0)
                if grid > 0:
                    team_data[team_name]["grid_positions"].append(grid)
                    team_data[team_name]["positions_gained"].append(grid - pos)

    if not team_data:
        return {}

    raw: Dict[str, Dict] = {}
    for name, data in team_data.items():
        avg_finish   = _mean(data["finish_positions"])
        avg_grid     = _mean(data["grid_positions"])
        avg_gained   = _mean(data["positions_gained"])
        reliability  = _mean(data["finishes"])
        # Invert positions (lower = better) to a score (higher = better)
        raw[name] = {
            "grid_score":    -avg_grid,   # lower grid pos number = better
            "race_score":    -avg_finish,
            "gained_score":  avg_gained,
            "reliability":   reliability,
        }

    grid_norm    = _normalize_dict({n: v["grid_score"]   for n, v in raw.items()}, SCALE_MIN, SCALE_MAX_TEAM)
    race_norm    = _normalize_dict({n: v["race_score"]   for n, v in raw.items()}, SCALE_MIN, SCALE_MAX_TEAM)
    gained_norm  = _normalize_dict({n: v["gained_score"] for n, v in raw.items()}, SCALE_MIN, SCALE_MAX_TEAM)
    rel_norm     = _normalize_dict({n: v["reliability"]  for n, v in raw.items()}, SCALE_MIN, SCALE_MAX_TEAM)

    ratings: Dict[str, Dict] = {}
    for name in raw:
        overall = round(
            0.30 * grid_norm[name]
            + 0.40 * race_norm[name]
            + 0.20 * gained_norm[name]
            + 0.10 * rel_norm[name],
            4,
        )
        overall = min(max(overall, SCALE_MIN), SCALE_MAX_TEAM)
        ratings[name] = {
            "overall_performance": overall,
            "qualifying_pace":     grid_norm[name],
            "race_pace":           race_norm[name],
            "reliability":         rel_norm[name],
        }

    return ratings


# ── Blending ──────────────────────────────────────────────────────────────────

def blend_with_prior(
    prior: float,
    current: float,
    n_races: int,
    virtual_races: int = PRIOR_VIRTUAL_RACES,
) -> float:
    """
    Bayesian-style blend of a prior rating with observed current rating.

    confidence = n_races / (n_races + virtual_races)
    blended    = prior * (1 - confidence) + current * confidence
    """
    confidence = n_races / (n_races + virtual_races)
    blended = prior * (1 - confidence) + current * confidence
    return round(blended, 4)


# ── Persistence ───────────────────────────────────────────────────────────────

def save_computed_ratings(driver_ratings: Dict, team_ratings: Dict) -> None:
    """Write computed ratings to config/computed_ratings.json."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    payload = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "drivers": driver_ratings,
        "teams": team_ratings,
    }
    with open(COMPUTED_RATINGS_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info("Saved computed ratings to %s", COMPUTED_RATINGS_PATH)
