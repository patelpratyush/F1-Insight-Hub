from app.core.f1_ratings import (
    compute_driver_scores, compute_driver_scores_with_breakdown,
)

DRIVER_MAP = {"AAA": "Alice Aaa", "BBB": "Bob Bbb"}
DRIVER_STANDINGS = {
    "AAA": {"points": 100, "position": 1, "team": "Alpha", "wins": 5},
    "BBB": {"points": 20, "position": 5, "team": "Beta", "wins": 0},
}
CONSTRUCTOR_STANDINGS = {
    "Alpha": {"points": 200, "position": 1},
    "Beta": {"points": 50, "position": 4},
}


class TestComputeDriverScores:
    def test_leader_scores_higher_than_backmarker(self):
        scores = compute_driver_scores(DRIVER_MAP, DRIVER_STANDINGS, CONSTRUCTOR_STANDINGS)
        assert scores["AAA"] > scores["BBB"]

    def test_scores_bounded(self):
        scores = compute_driver_scores(DRIVER_MAP, DRIVER_STANDINGS, CONSTRUCTOR_STANDINGS)
        for s in scores.values():
            assert 0.0 < s <= 1.0


class TestComputeDriverScoresWithBreakdown:
    def test_breakdown_matches_plain_scores(self):
        """The plain compute_driver_scores() must equal the .score field here."""
        plain = compute_driver_scores(DRIVER_MAP, DRIVER_STANDINGS, CONSTRUCTOR_STANDINGS)
        breakdown = compute_driver_scores_with_breakdown(
            DRIVER_MAP, DRIVER_STANDINGS, CONSTRUCTOR_STANDINGS,
        )
        for code in DRIVER_MAP:
            assert breakdown[code]["score"] == plain[code]

    def test_breakdown_has_all_factors(self):
        breakdown = compute_driver_scores_with_breakdown(
            DRIVER_MAP, DRIVER_STANDINGS, CONSTRUCTOR_STANDINGS,
        )
        for code in DRIVER_MAP:
            factors = breakdown[code]
            for key in ("base_skill", "team_mult", "form_factor", "weather_mod", "track_mod"):
                assert key in factors

    def test_score_is_product_of_factors(self):
        breakdown = compute_driver_scores_with_breakdown(
            DRIVER_MAP, DRIVER_STANDINGS, CONSTRUCTOR_STANDINGS,
        )
        for code in DRIVER_MAP:
            b = breakdown[code]
            expected = round(
                b["base_skill"] * b["team_mult"] * b["form_factor"] * b["weather_mod"] * b["track_mod"],
                4,
            )
            assert abs(b["score"] - expected) < 1e-6 or b["score"] == 1.0  # score is clamped at 1.0
