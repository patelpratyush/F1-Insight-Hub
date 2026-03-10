# Data-Driven Driver & Team Ratings Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute driver and team ratings from real race results (2025 teammate-normalized for drivers, 2026 recency-weighted for teams) and blend with hand-authored prior using a confidence weight that grows as the 2026 season progresses.

**Architecture:** A new `RatingsEngine` module (`backend/app/core/ratings_engine.py`) computes and writes `backend/config/computed_ratings.json` on startup and every 30 min. `CacheService` calls the sync `recompute()` function directly from its async lifecycle methods (acceptable: CPU + local file write, no network I/O, completes in <100ms). `f1_ratings.py` reads `computed_ratings.json` first, falls back to the hand-authored JSON files if absent.

**Tech Stack:** Python stdlib only (json, os, collections, datetime) + existing CacheService data — no new API calls needed. `grid` field in existing race results serves as qualifying proxy. pytest for tests.

**Spec:** `docs/superpowers/specs/2026-03-10-data-driven-ratings-design.md`

---

## Chunk 1: RatingsEngine core (`ratings_engine.py`)

### Task 1: Test infrastructure

**Files:**
- Create: `backend/requirements-dev.txt`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_ratings_engine.py`

- [ ] **Step 1: Create requirements-dev.txt**

`backend/requirements-dev.txt`:
```
pytest>=8.0.0
```

- [ ] **Step 2: Install pytest**

```bash
pip install pytest
```

- [ ] **Step 3: Create test directory and fixtures file**

```bash
mkdir -p backend/tests && touch backend/tests/__init__.py
```

`backend/tests/test_ratings_engine.py`:
```python
import pytest
from app.core.ratings_engine import compute_driver_ratings, compute_team_ratings, blend_with_prior

# ---------------------------------------------------------------------------
# Fixtures — two teams, four drivers, two races
# ---------------------------------------------------------------------------
# Alpha: AAA (good) always beats BBB (weak)
# Beta:  CCC (mid) vs DDD (mid) — evenly matched
# ---------------------------------------------------------------------------
RACE_1 = {
    "round": 1, "raceName": "Test GP", "date": "2025-03-16",
    "results": [
        {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 1, "position": 1,  "status": "Finished", "points": 25},
        {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 3, "position": 4,  "status": "Finished", "points": 12},
        {"code": "CCC", "name": "Carl Ccc",  "team": "Beta",  "grid": 2, "position": 2,  "status": "Finished", "points": 18},
        {"code": "DDD", "name": "Dave Ddd",  "team": "Beta",  "grid": 4, "position": 3,  "status": "Finished", "points": 15},
    ]
}
RACE_2 = {
    "round": 2, "raceName": "Test GP 2", "date": "2025-03-23",
    "results": [
        {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 1,  "position": 1,  "status": "Finished", "points": 25},
        {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 4,  "position": 20, "status": "Retired",  "points": 0},
        {"code": "CCC", "name": "Carl Ccc",  "team": "Beta",  "grid": 3,  "position": 3,  "status": "Finished", "points": 15},
        {"code": "DDD", "name": "Dave Ddd",  "team": "Beta",  "grid": 2,  "position": 4,  "status": "Finished", "points": 12},
    ]
}
RESULTS_2025 = [RACE_1, RACE_2]
# Use a single race for 2026 team tests (Australia equivalent)
RESULTS_2026 = [RACE_1]
```

- [ ] **Step 4: Verify test file is importable (will fail — module doesn't exist yet)**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py -x 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'app.core.ratings_engine'`

- [ ] **Step 5: Commit**

```bash
git add backend/requirements-dev.txt backend/tests/
git commit -m "test: add ratings engine test fixtures and dev dependencies"
```

---

### Task 2: Driver ratings computation

**Files:**
- Create: `backend/app/core/ratings_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_ratings_engine.py`:
```python
class TestDriverRatings:
    def test_ordering(self):
        """AAA beats BBB in every race — AAA must score higher."""
        ratings = compute_driver_ratings(RESULTS_2025)
        assert ratings["Alice Aaa"]["overall_skill"] > ratings["Bob Bbb"]["overall_skill"]

    def test_range(self):
        """All ratings must be in [0.60, 0.98]."""
        ratings = compute_driver_ratings(RESULTS_2025)
        for name, r in ratings.items():
            assert 0.60 <= r["overall_skill"] <= 0.98, f"{name}: {r['overall_skill']}"

    def test_dnf_excluded_from_race_delta(self):
        """BBB DNFs race 2 — both drivers excluded from race_delta for that race.
        AAA's race_delta should come from race 1 only (still positive)."""
        ratings = compute_driver_ratings(RESULTS_2025)
        # AAA still beats BBB even with BBB's race 2 DNF excluded
        assert ratings["Alice Aaa"]["overall_skill"] > ratings["Bob Bbb"]["overall_skill"]

    def test_required_keys(self):
        """Each driver entry has all four required rating keys."""
        ratings = compute_driver_ratings(RESULTS_2025)
        required = {"overall_skill", "wet_skill", "race_craft", "strategy_execution"}
        for name, r in ratings.items():
            assert required <= r.keys(), f"{name} missing keys"

    def test_empty_results(self):
        """No results → empty dict, no error."""
        assert compute_driver_ratings([]) == {}

    def test_pit_lane_start_excluded(self):
        """Grid position 0 (pit lane) excluded from grid delta calculation."""
        race = {
            "round": 1, "raceName": "PL GP", "date": "2025-01-01",
            "results": [
                {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 0,  "position": 3, "status": "Finished", "points": 15},
                {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 5,  "position": 5, "status": "Finished", "points": 10},
            ]
        }
        # Should not crash — grid delta for this race is skipped
        ratings = compute_driver_ratings([race])
        assert "Alice Aaa" in ratings
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py -x -v 2>&1 | head -20
```

Expected: `ImportError` — `ratings_engine` not defined.

- [ ] **Step 3: Create ratings_engine.py with helpers and compute_driver_ratings()**

Create `backend/app/core/ratings_engine.py`:
```python
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
```

- [ ] **Step 4: Run driver tests**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py::TestDriverRatings -v 2>&1 | tail -15
```

Expected: all 6 pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/ratings_engine.py backend/tests/test_ratings_engine.py
git commit -m "feat: driver ratings engine — teammate-normalized grid + race deltas"
```

---

### Task 3: Team ratings computation

**Files:**
- Modify: `backend/app/core/ratings_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_ratings_engine.py`:
```python
class TestTeamRatings:
    def test_ordering(self):
        """
        In RACE_1: Alpha avg grid = (1+3)/2 = 2.0, Beta avg grid = (2+4)/2 = 3.0.
        Alpha also has better avg finish: (1+4)/2 = 2.5 vs Beta (2+3)/2 = 2.5 (equal).
        Grid component alone favors Alpha → Alpha dry_pace >= Beta dry_pace.
        """
        ratings = compute_team_ratings(RESULTS_2026)
        assert ratings["Alpha"]["dry_pace"] >= ratings["Beta"]["dry_pace"]

    def test_range(self):
        """All team ratings in [0.60, 0.97]."""
        ratings = compute_team_ratings(RESULTS_2026)
        for team, r in ratings.items():
            for key in ("dry_pace", "wet_pace", "strategy", "reliability"):
                assert 0.60 <= r[key] <= 0.97, f"{team}.{key} = {r[key]}"

    def test_required_keys(self):
        ratings = compute_team_ratings(RESULTS_2026)
        required = {"dry_pace", "wet_pace", "strategy", "reliability"}
        for team, r in ratings.items():
            assert required <= r.keys()

    def test_reliability_all_finish(self):
        """When all drivers finish, reliability is in valid range (equal teams → midpoint)."""
        ratings = compute_team_ratings(RESULTS_2026)
        for team in ("Alpha", "Beta"):
            assert 0.60 <= ratings[team]["reliability"] <= 0.97

    def test_reliability_dnf_penalized(self):
        """Team with DNF gets lower reliability than team with perfect finish."""
        race = {
            "round": 1, "raceName": "DNF GP", "date": "2026-03-01",
            "results": [
                {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 1, "position": 1,  "status": "Finished", "points": 25},
                {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 2, "position": 20, "status": "Retired",  "points": 0},
                {"code": "CCC", "name": "Carl Ccc",  "team": "Beta",  "grid": 3, "position": 3,  "status": "Finished", "points": 15},
                {"code": "DDD", "name": "Dave Ddd",  "team": "Beta",  "grid": 4, "position": 4,  "status": "Finished", "points": 12},
            ]
        }
        ratings = compute_team_ratings([race])
        # Alpha: 1/2 finishes = 0.5 reliability, Beta: 2/2 = 1.0
        assert ratings["Beta"]["reliability"] > ratings["Alpha"]["reliability"]

    def test_recency_weight(self):
        """Team with bad race 1 but dominant race 2 should end up with good score."""
        race_a = {
            "round": 1, "raceName": "Race A", "date": "2026-03-01",
            "results": [
                {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 9,  "position": 9,  "status": "Finished", "points": 2},
                {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 10, "position": 10, "status": "Finished", "points": 1},
            ]
        }
        race_b = {
            "round": 2, "raceName": "Race B", "date": "2026-03-08",
            "results": [
                {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 1, "position": 1, "status": "Finished", "points": 25},
                {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 2, "position": 2, "status": "Finished", "points": 18},
            ]
        }
        rating_2races = compute_team_ratings([race_a, race_b])
        rating_bad    = compute_team_ratings([race_a])
        # Dominant race 2 lifts the 2-race result above the bad-only result
        assert rating_2races["Alpha"]["dry_pace"] > rating_bad["Alpha"]["dry_pace"]

    def test_empty_results(self):
        assert compute_team_ratings([]) == {}
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py::TestTeamRatings -x -v 2>&1 | head -15
```

Expected: `ImportError` — `compute_team_ratings` not defined.

- [ ] **Step 3: Implement compute_team_ratings()**

Add to `backend/app/core/ratings_engine.py`:
```python
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
    neg_grid  = {t: -team_grid.get(t, 20)  for t in team_seen}
    neg_race  = {t: -team_race.get(t, 20)  for t in team_seen}
    gained    = {t:  team_gained.get(t, 0) for t in team_seen}
    raw_rel   = {
        t: team_finishes.get(t, 0) / max(team_starts.get(t, 1), 1)
        for t in team_seen
    }

    grid_norm = _normalize_dict(neg_grid, SCALE_MIN, SCALE_MAX_TEAM)
    race_norm = _normalize_dict(neg_race, SCALE_MIN, SCALE_MAX_TEAM)
    gained_norm = _normalize_dict(gained, SCALE_MIN, SCALE_MAX_TEAM)
    rel_norm    = _normalize_dict(raw_rel, SCALE_MIN, SCALE_MAX_TEAM)

    ratings: Dict[str, Dict] = {}
    for team in team_seen:
        dry = round(0.6 * grid_norm[team] + 0.4 * race_norm[team], 4)
        dry = min(max(dry, SCALE_MIN), SCALE_MAX_TEAM)
        ratings[team] = {
            "dry_pace":    dry,
            "wet_pace":    round(dry * 0.97, 4),
            "strategy":    round(gained_norm[team], 4),
            "reliability": round(rel_norm[team], 4),
        }

    return ratings
```

- [ ] **Step 4: Run all tests so far**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py -v 2>&1 | tail -20
```

Expected: all 13 tests pass, 0 failures.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/ratings_engine.py backend/tests/test_ratings_engine.py
git commit -m "feat: team ratings engine — recency-weighted grid + race + reliability"
```

---

### Task 4: Confidence blending + recompute() output

**Files:**
- Modify: `backend/app/core/ratings_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_ratings_engine.py`:
```python
class TestBlendWithPrior:
    def test_zero_confidence_uses_prior(self):
        """With 0 races, result = prior entirely."""
        computed = {"drivers": {"Alice Aaa": {"overall_skill": 0.90}}, "teams": {}}
        prior_d  = {"Alice Aaa": {"overall_skill": 0.70, "wet_skill": 0.68, "race_craft": 0.68, "strategy_execution": 0.68}}
        result   = blend_with_prior(computed, prior_d, {}, n_2026_races=0)
        assert result["drivers"]["Alice Aaa"]["overall_skill"] == pytest.approx(0.70, abs=0.001)

    def test_confidence_grows_with_races(self):
        """More races → computed value weighted more heavily."""
        computed = {"drivers": {"Alice Aaa": {"overall_skill": 1.0, "wet_skill": 1.0, "race_craft": 1.0, "strategy_execution": 1.0}}, "teams": {}}
        prior_d  = {"Alice Aaa": {"overall_skill": 0.0, "wet_skill": 0.0, "race_craft": 0.0, "strategy_execution": 0.0}}
        r1  = blend_with_prior(computed, prior_d, {}, n_2026_races=1)
        r10 = blend_with_prior(computed, prior_d, {}, n_2026_races=10)
        assert r10["drivers"]["Alice Aaa"]["overall_skill"] > r1["drivers"]["Alice Aaa"]["overall_skill"]

    def test_driver_absent_from_prior_uses_default(self):
        """Driver in computed but not in prior gets default 0.70 at confidence=0."""
        computed = {"drivers": {"New Driver": {"overall_skill": 0.95, "wet_skill": 0.90, "race_craft": 0.88, "strategy_execution": 0.85}}, "teams": {}}
        result   = blend_with_prior(computed, {}, {}, n_2026_races=0)
        # confidence=0 → w_comp=0, w_prior=1 → 1.0 × default(0.70)
        assert result["drivers"]["New Driver"]["overall_skill"] == pytest.approx(0.70, abs=0.001)

    def test_meta_block_present(self):
        """Output includes _meta with required keys."""
        result = blend_with_prior({"drivers": {}, "teams": {}}, {}, {}, n_2026_races=3)
        assert "_meta" in result
        for key in ("generated_at", "n_2026_races", "confidence", "method"):
            assert key in result["_meta"]
        assert result["_meta"]["n_2026_races"] == 3

    def test_confidence_formula(self):
        """confidence = n / (n + PRIOR_VIRTUAL_RACES)  with PRIOR_VIRTUAL_RACES=4."""
        result = blend_with_prior({"drivers": {}, "teams": {}}, {}, {}, n_2026_races=4)
        assert result["_meta"]["confidence"] == pytest.approx(0.50, abs=0.001)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py::TestBlendWithPrior -x -v 2>&1 | head -15
```

Expected: `ImportError`

- [ ] **Step 3: Implement blend_with_prior() and recompute()**

Add to `backend/app/core/ratings_engine.py`:
```python
def blend_with_prior(
    computed: Dict,
    prior_drivers: Dict[str, Dict],
    prior_teams: Dict[str, Dict],
    n_2026_races: int,
) -> Dict:
    """
    Blend computed ratings with hand-authored prior using confidence weighting.
    confidence = n_2026_races / (n_2026_races + PRIOR_VIRTUAL_RACES)

    Missing values always fall back to 0.70 (the midfield default).
    This ensures drivers absent from prior at confidence=0 still get 0.70, not
    the computed value — so zero-data confidence truly means "use prior/default".
    """
    confidence = n_2026_races / (n_2026_races + PRIOR_VIRTUAL_RACES)
    w_comp  = confidence
    w_prior = 1.0 - confidence
    _DEFAULT = 0.70

    driver_keys = {"overall_skill", "wet_skill", "race_craft", "strategy_execution"}
    team_keys   = {"dry_pace", "wet_pace", "strategy", "reliability"}

    all_drivers = set(computed.get("drivers", {}).keys()) | set(prior_drivers.keys())
    all_teams   = set(computed.get("teams", {}).keys())   | set(prior_teams.keys())

    blended_drivers: Dict[str, Dict] = {}
    for name in all_drivers:
        comp  = computed.get("drivers", {}).get(name, {})
        prior = prior_drivers.get(name, {})
        blended_drivers[name] = {
            key: round(
                w_comp  * comp.get(key,  _DEFAULT) +
                w_prior * prior.get(key, _DEFAULT),
                4,
            )
            for key in driver_keys
        }

    blended_teams: Dict[str, Dict] = {}
    for team in all_teams:
        comp  = computed.get("teams", {}).get(team, {})
        prior = prior_teams.get(team, {})
        blended_teams[team] = {
            key: round(
                w_comp  * comp.get(key,  _DEFAULT) +
                w_prior * prior.get(key, _DEFAULT),
                4,
            )
            for key in team_keys
        }

    return {
        "_meta": {
            "generated_at":  datetime.now(timezone.utc).isoformat(),
            "n_2026_races":  n_2026_races,
            "confidence":    round(confidence, 4),
            "method":        "teammate-normalized 2025 + recency-weighted 2026",
        },
        "drivers": blended_drivers,
        "teams":   blended_teams,
    }


def recompute(cache) -> None:
    """
    Main entry point. Called synchronously from CacheService.initialize()
    and _periodic_refresh() (CPU + local file write — safe to call from async context).

    Fetches 2025 + current-year results from cache, computes ratings,
    blends with hand-authored prior, writes config/computed_ratings.json.
    Failures are logged and swallowed — never crash the server over ratings.
    """
    try:
        results_2025 = cache.get_all_race_results(2025)
        results_current = cache.get_all_race_results(cache.current_year)
        n_current_races = len(results_current)

        computed_drivers = compute_driver_ratings(results_2025)      if results_2025      else {}
        computed_teams   = compute_team_ratings(results_current)      if results_current   else {}

        prior_drivers = _load_prior("fallback_driver_ratings.json", "drivers")
        prior_teams   = _load_prior("fallback_team_ratings.json",   "teams")

        blended = blend_with_prior(
            {"drivers": computed_drivers, "teams": computed_teams},
            prior_drivers,
            prior_teams,
            n_2026_races=n_current_races,
        )
        blended["_meta"]["n_2025_races"] = len(results_2025)

        tmp_path_str = COMPUTED_RATINGS_PATH + ".tmp"
        with open(tmp_path_str, "w") as f:
            json.dump(blended, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path_str, COMPUTED_RATINGS_PATH)  # atomic swap — safe concurrent reads

        logger.info(
            f"Ratings recomputed: {len(computed_drivers)} drivers, "
            f"{len(computed_teams)} teams, confidence={blended['_meta']['confidence']}"
        )
    except Exception as e:
        logger.error(f"Ratings recompute failed (predictions will use prior): {e}")


def _load_prior(filename: str, key: str) -> Dict[str, Dict]:
    path = os.path.join(CONFIG_DIR, filename)
    try:
        with open(path) as f:
            return json.load(f).get(key, {})
    except Exception:
        return {}
```

- [ ] **Step 4: Run all tests**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py -v 2>&1 | tail -25
```

Expected: all 18 tests pass, 0 failures.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/ratings_engine.py backend/tests/test_ratings_engine.py
git commit -m "feat: confidence blending + recompute() — writes computed_ratings.json"
```

---

## Chunk 2: Integration (CacheService + f1_ratings.py)

> **Prerequisite:** Chunk 1 (Tasks 1–4) must be complete. `backend/app/core/ratings_engine.py` must exist and export `recompute` before any step in this chunk is executed.

### Task 5: Wire recompute() into CacheService

**Files:**
- Modify: `backend/app/services/cache.py`

The `recompute()` function is synchronous (CPU + local file write). Calling it directly from `async` methods is safe here — it completes in <100ms and has no network I/O.

- [ ] **Step 1: Add import to cache.py**

In `backend/app/services/cache.py`, add after existing imports:
```python
from ..core.ratings_engine import recompute as _recompute_ratings
```

- [ ] **Step 2: Call recompute() at end of initialize()**

In `CacheService.initialize()`, add after `logger.info(f"CacheService initialized...")`:
```python
            _recompute_ratings(self)
```

The full updated `initialize()` after Step 2 (recompute call added outside the try):
```python
    async def initialize(self):
        """Fetch fresh data from Jolpica on startup, then start background refresh."""
        try:
            await self._load_year(self.current_year)
            self._initialized = True
            logger.info(f"CacheService initialized for {self.current_year}")
            self._update_fallback_configs(self.current_year)
        except Exception as e:
            if self._loaded_years:
                self._initialized = True
                logger.warning(f"API refresh failed, serving from SQLite: {e}")
            else:
                logger.error(f"Cache init failed (degraded mode): {e}")
        # Recompute outside both paths so it runs in happy path AND degraded mode.
        # recompute() is self-contained — it catches and logs its own failures.
        _recompute_ratings(self)
        self._refresh_task = asyncio.create_task(self._periodic_refresh())
```

- [ ] **Step 3: Also load 2025 data on startup**

The driver ratings need 2025 race results. Load it in its **own isolated try/except** after the main try block, so a 2025 API failure doesn't put the server into degraded mode or prevent `_recompute_ratings` from running.

Final `initialize()`:
```python
    async def initialize(self):
        """Fetch fresh data from Jolpica on startup, then start background refresh."""
        try:
            await self._load_year(self.current_year)
            self._initialized = True
            logger.info(f"CacheService initialized for {self.current_year}")
            self._update_fallback_configs(self.current_year)
        except Exception as e:
            if self._loaded_years:
                self._initialized = True
                logger.warning(f"API refresh failed, serving from SQLite: {e}")
            else:
                logger.error(f"Cache init failed (degraded mode): {e}")
        # Load 2025 for driver ratings — use ensure_year (respects SQLite cache,
        # won't re-fetch if already loaded) so we don't trigger 24 API calls on
        # every startup. Isolated try so 2025 failure doesn't affect main-year.
        if self.current_year != 2025:
            try:
                await self.ensure_year(2025)
            except Exception as e:
                logger.warning(f"Could not load 2025 data for driver ratings: {e}")
        # Recompute outside both paths so it runs in happy path AND degraded mode.
        _recompute_ratings(self)
        self._refresh_task = asyncio.create_task(self._periodic_refresh())
```

- [ ] **Step 4: Call recompute() in _periodic_refresh() after loading new results**

`_recompute_ratings` must be **outside** the `try` block so it always runs after data loading, not skipped when earlier lines throw. Pattern mirrors `initialize()`.

In `_periodic_refresh()`, restructure as follows:
```python
    async def _periodic_refresh(self):
        while True:
            await asyncio.sleep(1800)
            try:
                j = self._jolpica
                year = self.current_year
                data = await j.get_driver_standings(year)
                if data:
                    await self._put(f"driver_standings:{year}", data, TTL_STANDINGS)
                data = await j.get_constructor_standings(year)
                if data:
                    await self._put(f"constructor_standings:{year}", data, TTL_STANDINGS)
                await self._load_new_results(year)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Periodic refresh error: {e}")
            # Recompute outside the try — always runs even if data fetch partially failed.
            # recompute() catches and logs its own failures, so this never raises.
            _recompute_ratings(self)
```

- [ ] **Step 5: Verify computed_ratings.json is written on startup**

```bash
rm -f backend/config/computed_ratings.json
cd backend && timeout 90 uvicorn main:app --port 8001 --log-level warning 2>&1 | tail -5
python -m json.tool backend/config/computed_ratings.json | python -c "
import json, sys
d = json.load(sys.stdin)
assert '_meta' in d, 'missing _meta'
assert 'drivers' in d, 'missing drivers'
assert 'teams' in d, 'missing teams'
print('OK — confidence:', d['_meta']['confidence'], '  drivers:', len(d['drivers']), '  teams:', len(d['teams']))
"
```

Expected:
```
OK — confidence: 0.2  drivers: 20  teams: 10
```

- [ ] **Step 6: Verify computed_ratings.json content**

```bash
python -m json.tool backend/config/computed_ratings.json | head -20
```

Expected: valid JSON with `_meta`, `drivers`, `teams` keys.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/cache.py
git commit -m "feat: wire ratings recompute into CacheService startup and refresh"
```

---

### Task 6: f1_ratings.py reads computed ratings first

**Files:**
- Modify: `backend/app/core/f1_ratings.py`
- Test: `backend/tests/test_ratings_engine.py` (append `TestRatingsLoading` class)

- [ ] **Step 1: Write test for fallback preference**

Append to `backend/tests/test_ratings_engine.py` (file was created in Chunk 1 Task 1 and already has `import pytest` and `from app.core.ratings_engine import ...` at the top):
```python
class TestRatingsLoading:
    def test_computed_ratings_preferred(self, tmp_path, monkeypatch):
        """f1_ratings uses computed_ratings.json when it exists."""
        import json, os
        from app.core import f1_ratings

        computed = {
            "_meta": {"confidence": 0.5},
            "drivers": {"Max Verstappen": {"overall_skill": 0.99, "wet_skill": 0.99, "race_craft": 0.99, "strategy_execution": 0.99}},
            "teams": {}
        }
        computed_path = tmp_path / "computed_ratings.json"
        computed_path.write_text(json.dumps(computed))

        monkeypatch.setattr(f1_ratings, "_COMPUTED_PATH", str(computed_path))

        ratings = f1_ratings._load_driver_ratings()
        assert ratings["Max Verstappen"]["overall_skill"] == pytest.approx(0.99, abs=0.001)

    def test_fallback_used_when_no_computed(self, tmp_path, monkeypatch):
        """f1_ratings falls back to fallback_driver_ratings.json when computed absent."""
        from app.core import f1_ratings

        # Point computed path at a nonexistent file
        monkeypatch.setattr(f1_ratings, "_COMPUTED_PATH", str(tmp_path / "nonexistent.json"))

        ratings = f1_ratings._load_driver_ratings()
        # Should still return something from the fallback file
        assert len(ratings) > 0

    def test_computed_team_ratings_preferred(self, tmp_path, monkeypatch):
        """f1_ratings uses computed teams from computed_ratings.json when present."""
        import json
        from app.core import f1_ratings

        computed = {
            "_meta": {"confidence": 0.5},
            "drivers": {},
            "teams": {"McLaren": {"dry_pace": 0.91, "wet_pace": 0.88, "strategy": 0.85, "reliability": 0.92}},
        }
        computed_path = tmp_path / "computed_ratings.json"
        computed_path.write_text(json.dumps(computed))

        monkeypatch.setattr(f1_ratings, "_COMPUTED_PATH", str(computed_path))

        ratings = f1_ratings._load_team_ratings()
        assert ratings["McLaren"]["dry_pace"] == pytest.approx(0.91, abs=0.001)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_ratings_engine.py::TestRatingsLoading -x -v 2>&1 | head -15
```

Expected: `AttributeError` — `_COMPUTED_PATH` not defined yet.

- [ ] **Step 3: Update f1_ratings.py**

At the top of `backend/app/core/f1_ratings.py`, add after `CONFIG_DIR = ...`:
```python
_COMPUTED_PATH = os.path.join(CONFIG_DIR, "computed_ratings.json")
```

Replace the existing `_load_driver_ratings()`:
```python
def _load_driver_ratings() -> Dict[str, Dict]:
    # Prefer live-computed ratings; fall back to hand-authored JSON
    computed = _load_json_path(_COMPUTED_PATH)
    if computed.get("drivers"):
        return computed["drivers"]
    return _load_json("fallback_driver_ratings.json").get("drivers", {})
```

Replace the existing `_load_team_ratings()`:
```python
def _load_team_ratings() -> Dict[str, Dict]:
    computed = _load_json_path(_COMPUTED_PATH)
    if computed.get("teams"):
        return computed["teams"]
    return _load_json("fallback_team_ratings.json").get("teams", {})
```

Add a new helper `_load_json_path()` (loads by absolute path, not relative to CONFIG_DIR):
```python
def _load_json_path(path: str) -> Dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}
```

- [ ] **Step 4: Run all tests**

```bash
cd backend && python -m pytest tests/ -v 2>&1 | tail -25
```

Expected: all 21 tests pass, 0 failures.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/f1_ratings.py backend/tests/test_ratings_engine.py
git commit -m "feat: f1_ratings prefers computed_ratings.json over hand-authored fallback"
```

---

### Task 7: End-to-end smoke test + push

- [ ] **Step 1: Start server and hit the predict endpoint**

```bash
cd backend && uvicorn main:app --port 8001 --log-level warning &
sleep 15
curl -s -X POST http://localhost:8001/api/predict/race \
  -H "Content-Type: application/json" \
  -d '{"track": "Australian Grand Prix", "weather": "dry"}' \
  | python -m json.tool | head -30
```

Expected: valid JSON with `grid` array containing drivers with `win_probability`, `podium_probability`.

- [ ] **Step 2: Verify computed_ratings.json has sensible values**

```bash
python -m json.tool backend/config/computed_ratings.json | python -c "
import json, sys
d = json.load(sys.stdin)
print('confidence:', d['_meta']['confidence'])
print('n_2026_races:', d['_meta']['n_2026_races'])
drivers = d['drivers']
top3 = sorted(drivers.items(), key=lambda x: -x[1]['overall_skill'])[:3]
print('Top 3 drivers:')
for name, r in top3:
    print(f'  {name}: {r[\"overall_skill\"]}')
"
```

Expected: confidence > 0, top 3 are recognizable names, all values in [0.60, 0.98].

- [ ] **Step 3: Kill server, final commit, push**

```bash
kill %1 2>/dev/null || true
git add backend/app/core/ratings_engine.py \
      backend/app/services/cache.py \
      backend/app/core/f1_ratings.py \
      backend/tests/ \
      backend/requirements-dev.txt
git commit -m "feat: data-driven ratings engine — 2025 teammate-normalized + 2026 recency-weighted"
git push origin main
```
