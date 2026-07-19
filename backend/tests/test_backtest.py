from app.core.backtest import rating_concordance


class TestRatingConcordance:
    def test_perfect_agreement(self):
        """Scores in the same order as standings points -> 100% concordant."""
        scores = {"AAA": 0.9, "BBB": 0.7, "CCC": 0.5}
        standings = {
            "AAA": {"points": 100},
            "BBB": {"points": 60},
            "CCC": {"points": 20},
        }
        result = rating_concordance(scores, standings)
        assert result["concordant_pct"] == 1.0
        assert result["compared_pairs"] == 3

    def test_full_disagreement(self):
        """Scores in the exact opposite order -> 0% concordant."""
        scores = {"AAA": 0.5, "BBB": 0.7, "CCC": 0.9}
        standings = {
            "AAA": {"points": 100},
            "BBB": {"points": 60},
            "CCC": {"points": 20},
        }
        result = rating_concordance(scores, standings)
        assert result["concordant_pct"] == 0.0

    def test_ignores_drivers_missing_from_scores(self):
        scores = {"AAA": 0.9, "BBB": 0.7}
        standings = {
            "AAA": {"points": 100},
            "BBB": {"points": 60},
            "ZZZ": {"points": 999},  # not in scores, must be excluded
        }
        result = rating_concordance(scores, standings)
        assert result["compared_pairs"] == 1

    def test_ties_in_points_excluded(self):
        scores = {"AAA": 0.9, "BBB": 0.5}
        standings = {"AAA": {"points": 50}, "BBB": {"points": 50}}
        result = rating_concordance(scores, standings)
        assert result["compared_pairs"] == 0
        assert result["concordant_pct"] is None

    def test_fewer_than_two_drivers(self):
        result = rating_concordance({"AAA": 0.9}, {"AAA": {"points": 100}})
        assert result["concordant_pct"] is None
        assert result["compared_pairs"] == 0
