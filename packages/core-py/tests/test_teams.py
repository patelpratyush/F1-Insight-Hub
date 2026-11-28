from f1_core.teams import team_color


def test_known_team_color() -> None:
    assert team_color("mclaren") == "#FF8000"


def test_unknown_team_falls_back_to_f1_red() -> None:
    assert team_color("unknown") == "#E10600"
