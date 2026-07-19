from app.services.jolpica import _parse_duration


class TestParseDuration:
    def test_plain_seconds(self):
        assert _parse_duration("36.604") == 36.604

    def test_minutes_seconds(self):
        """Long pit stops (damage, penalties) come back as M:SS.mmm."""
        assert _parse_duration("1:14.773") == 74.773

    def test_none(self):
        assert _parse_duration(None) is None

    def test_empty_string(self):
        assert _parse_duration("") is None

    def test_garbage(self):
        assert _parse_duration("not a number") is None
