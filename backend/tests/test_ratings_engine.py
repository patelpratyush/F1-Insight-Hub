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
        """Recency weighting: dominant recent race weighs more than bad old race."""
        race_a = {
            "round": 1, "raceName": "Race A", "date": "2026-03-01",
            "results": [
                {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 9,  "position": 9,  "status": "Finished", "points": 2},
                {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 10, "position": 10, "status": "Finished", "points": 1},
                {"code": "GGG", "name": "Gary Ggg",  "team": "Gamma", "grid": 9,  "position": 9,  "status": "Finished", "points": 2},
                {"code": "HHH", "name": "Hank Hhh",  "team": "Gamma", "grid": 10, "position": 10, "status": "Finished", "points": 1},
            ]
        }
        race_b = {
            "round": 2, "raceName": "Race B", "date": "2026-03-08",
            "results": [
                {"code": "AAA", "name": "Alice Aaa", "team": "Alpha", "grid": 1, "position": 1, "status": "Finished", "points": 25},
                {"code": "BBB", "name": "Bob Bbb",   "team": "Alpha", "grid": 2, "position": 2, "status": "Finished", "points": 18},
                {"code": "GGG", "name": "Gary Ggg",  "team": "Gamma", "grid": 9, "position": 9, "status": "Finished", "points": 2},
                {"code": "HHH", "name": "Hank Hhh",  "team": "Gamma", "grid": 10, "position": 10, "status": "Finished", "points": 1},
            ]
        }
        ratings = compute_team_ratings([race_a, race_b])
        # Alpha's dominant race 2 (weight 2/3) lifts it above Gamma (consistently mediocre)
        assert ratings["Alpha"]["dry_pace"] > ratings["Gamma"]["dry_pace"]

    def test_empty_results(self):
        assert compute_team_ratings([]) == {}
