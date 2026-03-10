"""Thin service layer over CacheService for race results."""
import logging
from typing import Dict, List, Optional
from ..services.cache import CacheService

logger = logging.getLogger(__name__)


class ResultsService:
    def __init__(self, cache: CacheService):
        self._c = cache

    def get_driver_standings(self, year: int) -> List[Dict]:
        return self._c.get_driver_standings(year)

    def get_constructor_standings(self, year: int) -> List[Dict]:
        return self._c.get_constructor_standings(year)

    def get_calendar(self, year: int) -> List[Dict]:
        return self._c.get_schedule(year)

    def get_next_race(self, year: int) -> Optional[Dict]:
        return self._c.get_next_race(year)

    def get_recent_races(self, year: int, limit: int = 5) -> List[Dict]:
        return self._c.get_race_summaries(year)[-limit:]

    def get_session_result(self, year: int, round_num: int) -> Optional[Dict]:
        return self._c.get_race_result(year, round_num)

    def get_season_stats(self, year: int) -> Dict:
        return self._c.get_season_stats(year)

    def get_upcoming_races(self, year: int) -> List[Dict]:
        return self._c.get_upcoming_races(year)
