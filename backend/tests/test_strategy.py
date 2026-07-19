from app.services.strategy import _simulate_strategy, _format_race_time


class TestFormatRaceTime:
    def test_formats_hours_minutes_seconds(self):
        assert _format_race_time(3723.456) == "1:02:03.456"

    def test_zero(self):
        assert _format_race_time(0) == "0:00:00.000"


class TestSimulateStrategy:
    def test_pit_stops_count_matches_stints_minus_one(self):
        result = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "MEDIUM", "HARD"], "dry")
        assert len(result["pit_stops"]) == 2
        assert len(result["stints"]) == 3

    def test_pit_stop_lap_matches_stint_boundary(self):
        result = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "HARD"], "dry")
        assert result["pit_stops"][0]["lap"] == result["stints"][0]["end_lap"]
        assert result["pit_stops"][0]["old_tire"] == "SOFT"
        assert result["pit_stops"][0]["new_tire"] == "HARD"

    def test_total_seconds_matches_total_time(self):
        result = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["MEDIUM", "HARD"], "dry")
        assert result["total_seconds"] == result["total_time"]

    def test_efficiency_score_bounded(self):
        result = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "MEDIUM", "HARD"], "dry")
        assert 0.0 <= result["efficiency_score"] <= 100.0

    def test_confidence_bounded(self):
        result = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "MEDIUM", "HARD"], "dry")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_more_pit_stops_increase_risk(self):
        one_stop = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "HARD"], "dry")
        three_stop = _simulate_strategy(
            "VER", "Monaco Grand Prix", 57, ["SOFT", "MEDIUM", "MEDIUM", "HARD"], "dry",
        )
        assert three_stop["risk_analysis"]["pit_stop_risk"] > one_stop["risk_analysis"]["pit_stop_risk"]

    def test_wet_weather_increases_risk(self):
        dry = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "HARD"], "dry")
        wet = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["WET", "WET"], "wet")
        assert wet["risk_analysis"]["weather_risk"] > dry["risk_analysis"]["weather_risk"]

    def test_timeline_covers_full_race(self):
        result = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "MEDIUM", "HARD"], "dry")
        assert result["timeline"][0]["lap_start"] == 1
        assert result["timeline"][-1]["lap_end"] == 57

    def test_stints_cover_full_race_without_gaps(self):
        result = _simulate_strategy("VER", "Monaco Grand Prix", 57, ["SOFT", "MEDIUM", "HARD"], "dry")
        stints = result["stints"]
        assert stints[0]["start_lap"] == 1
        assert stints[-1]["end_lap"] == 57
        for prev, nxt in zip(stints, stints[1:]):
            assert nxt["start_lap"] == prev["end_lap"] + 1
