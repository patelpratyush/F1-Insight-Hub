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
            "wet_skill":          round(min(max(overall * 0.97, SCALE_MIN), SCALE_MAX_DRIVER), 4),   # placeholder — no wet detection yet
            "race_craft":         race_craft,
            "strategy_execution": round((overall + race_craft) / 2, 4),
        }

    return ratings


# ── Team ratings ──────────────────────────────────────────────────────────────

def compute_team_ratings(results: List[Dict]) -> Dict[str, Dict]:
    """
    Compute team car performance ratings from race results using recency weighting.

    Weight for race i (0-indexed) of N total: (i+1) / sum(1..N)
    Oldest = lowest weight, most recent = highest weight.

    Metrics per team (weighted averages across races):
      grid_score  = weighted avg grid position of both drivers (lower = better)
      race_score  = weighted avg finish position of classified drivers (lower = better)
      gained      = weighted avg (grid_pos - finish_pos)  (higher = gained positions)
      reliability = classified_finishes / total_starts (unweighted)

    dry_pace = 0.6 × norm(−grid_score) + 0.4 × norm(−race_score)
    wet_pace = dry_pace × 0.97
    strategy = norm(gained)
    """
    n = len(results)
    if n == 0:
        return {}

    weight_sum = n * (n + 1) / 2
    weights = [(i + 1) / weight_sum for i in range(n)]

    team_grid:     Dict[str, float] = defaultdict(float)
    team_race:     Dict[str, float] = defaultdict(float)
    team_gained:   Dict[str, float] = defaultdict(float)
    team_starts:   Dict[str, int]   = defaultdict(int)
    team_finishes: Dict[str, int]   = defaultdict(int)
    team_seen:     set              = set()

    for w, race in zip(weights, results):
        teams: Dict[str, List[Dict]] = defaultdict(list)
        for r in race.get("results", []):
            if r.get("team"):
                teams[r["team"]].append(r)
                team_seen.add(r["team"])

        for team_name, drivers in teams.items():
            team_starts[team_name] += len(drivers)
            finishers = [d for d in drivers if d.get("status") == "Finished"]
            team_finishes[team_name] += len(finishers)

            if not finishers:
                continue

            valid_grids = [d.get("grid", 20) for d in drivers if d.get("grid", 0) > 0]
            avg_grid  = _mean(valid_grids) if valid_grids else 20.0
            avg_race  = _mean([d["position"] for d in finishers])
            avg_gained = avg_grid - avg_race  # positive = gained positions in race

            team_grid[team_name]   += w * avg_grid
            team_race[team_name]   += w * avg_race
            team_gained[team_name] += w * avg_gained

    if not team_seen:
        return {}

    # Negate grid and race scores so lower position → higher normalized value
    neg_grid  = {t: -team_grid[t]   for t in team_seen}
    neg_race  = {t: -team_race[t]   for t in team_seen}
    gained    = {t:  team_gained[t] for t in team_seen}
    raw_rel   = {
        t: team_finishes[t] / max(team_starts[t], 1)
        for t in team_seen
    }

    grid_norm   = _normalize_dict(neg_grid,  SCALE_MIN, SCALE_MAX_TEAM)
    race_norm   = _normalize_dict(neg_race,  SCALE_MIN, SCALE_MAX_TEAM)
    gained_norm = _normalize_dict(gained,    SCALE_MIN, SCALE_MAX_TEAM)
    rel_norm    = _normalize_dict(raw_rel,   SCALE_MIN, SCALE_MAX_TEAM)

    ratings: Dict[str, Dict] = {}
    for team in team_seen:
        dry = round(0.6 * grid_norm[team] + 0.4 * race_norm[team], 4)
        dry = min(max(dry, SCALE_MIN), SCALE_MAX_TEAM)
        ratings[team] = {
            "dry_pace":    dry,
            "wet_pace":    round(min(max(dry * 0.97, SCALE_MIN), SCALE_MAX_TEAM), 4),
            "strategy":    round(gained_norm[team], 4),
            "reliability": round(rel_norm[team], 4),
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
