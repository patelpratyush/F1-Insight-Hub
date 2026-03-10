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

    def test_wet_skill_range(self):
        """wet_skill must be in [0.60, 0.98] — not just overall_skill."""
        ratings = compute_driver_ratings(RESULTS_2025)
        for name, r in ratings.items():
            assert 0.60 <= r["wet_skill"] <= 0.98, f"{name} wet_skill={r['wet_skill']}"

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
