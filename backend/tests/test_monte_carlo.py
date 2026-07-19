from app.core.monte_carlo import simulate_race


class TestSimulateRace:
    def test_empty_input(self):
        assert simulate_race({}) == []

    def test_higher_score_wins_more_often(self):
        scores = {"AAA": 0.95, "BBB": 0.5}
        results = simulate_race(scores, n_iterations=2000, chaos_factor=0.1)
        by_driver = {r["driver"]: r for r in results}
        assert by_driver["AAA"]["win_pct"] > by_driver["BBB"]["win_pct"]
        assert by_driver["AAA"]["median_pos"] < by_driver["BBB"]["median_pos"]

    def test_percentile_range_is_ordered(self):
        scores = {"AAA": 0.9, "BBB": 0.7, "CCC": 0.5}
        results = simulate_race(scores, n_iterations=1000)
        for r in results:
            assert r["p10_pos"] <= r["p90_pos"]
            assert r["p10_pos"] >= 1
            assert r["p90_pos"] <= len(scores)

    def test_probabilities_bounded(self):
        scores = {"AAA": 0.9, "BBB": 0.7, "CCC": 0.5}
        results = simulate_race(scores, n_iterations=500)
        for r in results:
            assert 0.0 <= r["win_pct"] <= 1.0
            assert 0.0 <= r["podium_pct"] <= 1.0
            assert r["win_pct"] <= r["podium_pct"]  # can't win more than podium

    def test_results_sorted_by_median_position(self):
        scores = {"AAA": 0.9, "BBB": 0.7, "CCC": 0.5}
        results = simulate_race(scores, n_iterations=500)
        positions = [r["median_pos"] for r in results]
        assert positions == sorted(positions)

    def test_predicted_position_is_rank(self):
        scores = {"AAA": 0.9, "BBB": 0.7, "CCC": 0.5}
        results = simulate_race(scores, n_iterations=500)
        assert [r["predicted_position"] for r in results] == list(range(1, len(results) + 1))
