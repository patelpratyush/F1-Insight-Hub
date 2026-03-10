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
