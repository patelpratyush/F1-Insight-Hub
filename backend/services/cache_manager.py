#!/usr/bin/env python3
"""
Centralized F1 Data Cache Manager
Fetches metadata from Jolpica-F1 API (Ergast replacement) and caches in memory.
Replaces all hardcoded race results, standings, schedules, and driver/team data.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"


@dataclass
class CacheEntry:
    data: Any
    fetched_at: datetime
    ttl_seconds: int  # 0 = permanent (never expires)

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds == 0:
            return False
        elapsed = (datetime.now(timezone.utc) - self.fetched_at).total_seconds()
        return elapsed > self.ttl_seconds


class CacheManager:
    """Centralized F1 data cache fed by Jolpica-F1 API."""

    TTL_PERMANENT = 0
    TTL_STANDINGS = 3600      # 1 hour
    TTL_SCHEDULE = 86400      # 24 hours
    TTL_DRIVERS = 86400       # 24 hours

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._refresh_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        self._current_year: int = datetime.now(timezone.utc).year
        self._loaded_years: set = set()
        self._loading_locks: Dict[int, asyncio.Lock] = {}

    # ── Lifecycle ─────────────────────────────────────────────────

    async def initialize(self, year: int = None):
        """Called from FastAPI startup. Fetches all data for the given year."""
        if year is None:
            year = self._current_year
        self._current_year = year
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        try:
            await self._full_load(year)
            self._loaded_years.add(year)
            self._initialized = True
            logger.info(f"CacheManager initialized for {year}")
        except Exception as e:
            logger.error(f"CacheManager init failed (degraded mode): {e}")
        self._refresh_task = asyncio.create_task(self._periodic_refresh(year))

    async def shutdown(self):
        """Called from FastAPI shutdown."""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
        logger.info("CacheManager shut down")

    # ── Public Getters (instant, from cache) ──────────────────────

    def get_schedule(self, year: int) -> List[Dict]:
        return self._get(f"schedule:{year}", [])

    def get_drivers(self, year: int) -> List[Dict]:
        return self._get(f"drivers:{year}", [])

    def get_constructors(self, year: int) -> List[Dict]:
        return self._get(f"constructors:{year}", [])

    def get_driver_standings(self, year: int) -> List[Dict]:
        return self._get(f"driver_standings:{year}", [])

    def get_constructor_standings(self, year: int) -> List[Dict]:
        return self._get(f"constructor_standings:{year}", [])

    def get_race_result(self, year: int, round_num: int) -> Optional[Dict]:
        return self._get(f"race_result:{year}:{round_num}", None)

    def get_all_race_results(self, year: int) -> List[Dict]:
        """Return all cached race results for a year, sorted by round."""
        results = []
        schedule = self.get_schedule(year)
        for race in schedule:
            rnd = race.get("round")
            result = self.get_race_result(year, rnd)
            if result:
                results.append(result)
        return results

    def get_completed_races(self, year: int) -> List[Dict]:
        """Return schedule entries for races that have results cached."""
        completed = []
        schedule = self.get_schedule(year)
        for race in schedule:
            rnd = race.get("round")
            if self._cache.get(f"race_result:{year}:{rnd}"):
                completed.append(race)
        return completed

    def get_next_race(self, year: int) -> Optional[Dict]:
        """Return the first future race from the schedule."""
        schedule = self.get_schedule(year)
        now = datetime.now(timezone.utc).date()
        for race in schedule:
            try:
                race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                if race_date > now:
                    return race
            except (KeyError, ValueError):
                continue
        return None

    def get_driver_name(self, code: str, year: int) -> str:
        """Look up full driver name by code."""
        for d in self.get_drivers(year):
            if d.get("code") == code:
                return d.get("name", code)
        return code

    def get_driver_team(self, code: str, year: int) -> str:
        """Look up driver team by code."""
        standings = self.get_driver_standings(year)
        for s in standings:
            if s.get("driver") == code:
                return s.get("team", "Unknown")
        return "Unknown"

    def get_driver_code_map(self, year: int) -> Dict[str, str]:
        """Return {code: full_name} mapping."""
        return {d["code"]: d["name"] for d in self.get_drivers(year) if "code" in d}

    def get_latest_race(self, year: int) -> Optional[Dict]:
        """Return the most recently completed race result."""
        results = self.get_all_race_results(year)
        return results[-1] if results else None

    def get_season_statistics(self, year: int) -> Dict:
        """Derive season stats from cached schedule."""
        schedule = self.get_schedule(year)
        completed = self.get_completed_races(year)
        return {
            "total_races": len(schedule),
            "completed_races": len(completed),
            "remaining_races": len(schedule) - len(completed),
            "season_complete": len(completed) == len(schedule) and len(schedule) > 0,
        }

    def get_performance_trends(self, year: int, all_races: bool = False) -> List[Dict]:
        """Build per-race points breakdown from cached race results."""
        results = self.get_all_race_results(year)
        if not results:
            return []
        if not all_races:
            results = results[-5:]

        trends = []
        for race_result in results:
            race_name = race_result.get("raceName", "").replace(" Grand Prix", "").strip()
            race_data = {"race": race_name}
            for driver_result in race_result.get("results", []):
                code = driver_result.get("code", "")
                if code:
                    race_data[code] = driver_result.get("points", 0)
            trends.append(race_data)
        return trends

    def get_points_breakdown(self, year: int) -> Dict[str, Dict]:
        """Build {driver_code: {total, per_round}} from cached results."""
        results = self.get_all_race_results(year)
        points_map: Dict[str, Dict] = {}

        for race_result in results:
            round_num = race_result.get("round", 0)
            for dr in race_result.get("results", []):
                code = dr.get("code", "")
                pts = dr.get("points", 0)
                if not code:
                    continue
                if code not in points_map:
                    points_map[code] = {"total": 0, "per_round": {}}
                points_map[code]["total"] += pts
                points_map[code]["per_round"][round_num] = pts

        return points_map

    def get_race_summaries(self, year: int) -> List[Dict]:
        """Build race summaries (podium format) from cached results."""
        results = self.get_all_race_results(year)
        summaries = []
        for race_result in results:
            podium = []
            for dr in race_result.get("results", [])[:3]:
                podium.append({
                    "position": dr.get("position", 0),
                    "driver": dr.get("code", ""),
                    "name": dr.get("name", ""),
                    "team": dr.get("team", ""),
                    "time": dr.get("time", ""),
                })
            summaries.append({
                "race_name": race_result.get("raceName", ""),
                "round": race_result.get("round", 0),
                "date": race_result.get("date", ""),
                "location": race_result.get("location", ""),
                "podium": podium,
            })
        return summaries

    def get_upcoming_races(self, year: int) -> List[Dict]:
        """Return future races from the schedule."""
        schedule = self.get_schedule(year)
        now = datetime.now(timezone.utc).date()
        upcoming = []
        for race in schedule:
            try:
                race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                if race_date > now:
                    upcoming.append(race)
            except (KeyError, ValueError):
                continue
        return upcoming

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def ensure_year_loaded(self, year: int):
        """Load data for a year on-demand if not already cached."""
        if year in self._loaded_years:
            return
        if year not in self._loading_locks:
            self._loading_locks[year] = asyncio.Lock()
        async with self._loading_locks[year]:
            if year in self._loaded_years:
                return  # Another coroutine loaded it while we waited
            logger.info(f"On-demand loading data for {year}...")
            await self._full_load(year)
            self._loaded_years.add(year)

    # ── Private Helpers ───────────────────────────────────────────

    def _get(self, key: str, default: Any) -> Any:
        """Return cached data, even if expired (stale-while-revalidate)."""
        entry = self._cache.get(key)
        if entry is None:
            return default
        return entry.data

    def _set(self, key: str, data: Any, ttl: int):
        self._cache[key] = CacheEntry(
            data=data,
            fetched_at=datetime.now(timezone.utc),
            ttl_seconds=ttl,
        )

    # ── Private: API Fetch Methods ────────────────────────────────

    async def _api_get(self, path: str) -> Optional[Dict]:
        """HTTP GET from Jolpica API with error handling."""
        if not self._session:
            return None
        url = f"{JOLPICA_BASE}/{path}"
        try:
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    logger.warning(f"Jolpica rate limited on {path}, backing off")
                    await asyncio.sleep(5)
                    return None
                else:
                    logger.warning(f"Jolpica {path} returned {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Jolpica fetch error for {path}: {e}")
            return None

    async def _fetch_schedule(self, year: int):
        """Fetch and cache season schedule."""
        data = await self._api_get(f"{year}.json")
        if not data:
            return
        try:
            races_raw = data["MRData"]["RaceTable"]["Races"]
            schedule = []
            for race in races_raw:
                schedule.append({
                    "round": int(race["round"]),
                    "race_name": race["raceName"],
                    "date": race["date"],
                    "circuit": race["Circuit"]["circuitName"],
                    "location": race["Circuit"]["Location"].get("locality", ""),
                    "country": race["Circuit"]["Location"].get("country", ""),
                })
            self._set(f"schedule:{year}", schedule, self.TTL_SCHEDULE)
            logger.info(f"Cached schedule for {year}: {len(schedule)} races")
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to parse schedule for {year}: {e}")

    async def _fetch_drivers(self, year: int):
        """Fetch and cache driver list."""
        data = await self._api_get(f"{year}/drivers.json?limit=30")
        if not data:
            return
        try:
            drivers_raw = data["MRData"]["DriverTable"]["Drivers"]
            drivers = []
            for d in drivers_raw:
                drivers.append({
                    "id": d.get("driverId", ""),
                    "code": d.get("code", ""),
                    "name": f"{d.get('givenName', '')} {d.get('familyName', '')}".strip(),
                    "number": d.get("permanentNumber", ""),
                    "nationality": d.get("nationality", ""),
                })
            self._set(f"drivers:{year}", drivers, self.TTL_DRIVERS)
            logger.info(f"Cached drivers for {year}: {len(drivers)} drivers")
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to parse drivers for {year}: {e}")

    async def _fetch_constructors(self, year: int):
        """Fetch and cache constructor list."""
        data = await self._api_get(f"{year}/constructors.json")
        if not data:
            return
        try:
            constructors_raw = data["MRData"]["ConstructorTable"]["Constructors"]
            constructors = []
            for c in constructors_raw:
                constructors.append({
                    "id": c.get("constructorId", ""),
                    "name": c.get("name", ""),
                    "nationality": c.get("nationality", ""),
                })
            self._set(f"constructors:{year}", constructors, self.TTL_DRIVERS)
            logger.info(f"Cached constructors for {year}: {len(constructors)}")
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to parse constructors for {year}: {e}")

    async def _fetch_driver_standings(self, year: int):
        """Fetch and cache driver championship standings."""
        data = await self._api_get(f"{year}/driverStandings.json")
        if not data:
            return
        try:
            standings_lists = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not standings_lists:
                return
            raw_standings = standings_lists[0]["DriverStandings"]
            standings = []
            for s in raw_standings:
                driver = s["Driver"]
                team = s["Constructors"][0]["name"] if s.get("Constructors") else "Unknown"
                standings.append({
                    "position": int(s["position"]),
                    "driver": driver.get("code", ""),
                    "name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "team": team,
                    "points": float(s["points"]),
                    "wins": int(s["wins"]),
                })
            self._set(f"driver_standings:{year}", standings, self.TTL_STANDINGS)
            logger.info(f"Cached driver standings for {year}: {len(standings)} drivers")
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Failed to parse driver standings for {year}: {e}")

    async def _fetch_constructor_standings(self, year: int):
        """Fetch and cache constructor championship standings."""
        data = await self._api_get(f"{year}/constructorStandings.json")
        if not data:
            return
        try:
            standings_lists = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not standings_lists:
                return
            raw_standings = standings_lists[0]["ConstructorStandings"]
            standings = []
            for s in raw_standings:
                constructor = s["Constructor"]
                standings.append({
                    "position": int(s["position"]),
                    "team_name": constructor.get("name", ""),
                    "points": float(s["points"]),
                    "wins": int(s["wins"]),
                })
            self._set(f"constructor_standings:{year}", standings, self.TTL_STANDINGS)
            logger.info(f"Cached constructor standings for {year}: {len(standings)}")
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Failed to parse constructor standings for {year}: {e}")

    async def _fetch_race_result(self, year: int, round_num: int):
        """Fetch and permanently cache a single race result."""
        data = await self._api_get(f"{year}/{round_num}/results.json")
        if not data:
            return
        try:
            races = data["MRData"]["RaceTable"]["Races"]
            if not races:
                return
            race = races[0]
            results_raw = race.get("Results", [])

            results = []
            for r in results_raw:
                driver = r["Driver"]
                constructor = r["Constructor"]
                time_str = r.get("Time", {}).get("time", "") if isinstance(r.get("Time"), dict) else ""
                results.append({
                    "position": int(r["position"]),
                    "code": driver.get("code", ""),
                    "name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "team": constructor.get("name", ""),
                    "points": float(r.get("points", 0)),
                    "time": time_str,
                    "status": r.get("status", ""),
                    "laps": int(r.get("laps", 0)),
                })

            # Extract fastest lap driver
            fastest_lap = {}
            for r in results_raw:
                fl = r.get("FastestLap")
                if fl and fl.get("rank") == "1":
                    fastest_lap = {
                        "driver": r["Driver"].get("code", ""),
                        "time": fl.get("Time", {}).get("time", ""),
                        "lap": fl.get("lap", ""),
                    }
                    break

            location = race.get("Circuit", {}).get("Location", {}).get("locality", "")

            result_entry = {
                "raceName": race.get("raceName", ""),
                "round": int(race.get("round", round_num)),
                "date": race.get("date", ""),
                "location": location,
                "results": results,
                "fastestLap": fastest_lap,
                "totalLaps": int(results[0]["laps"]) if results else 0,
            }

            self._set(f"race_result:{year}:{round_num}", result_entry, self.TTL_PERMANENT)
            logger.info(f"Cached race result: {year} R{round_num} {race.get('raceName', '')}")
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Failed to parse race result {year} R{round_num}: {e}")

    # ── Private: Bulk Load & Refresh ──────────────────────────────

    async def _full_load(self, year: int):
        """Load everything for a year. Called on startup."""
        logger.info(f"Starting full cache load for {year}...")

        # Fetch metadata first (these are fast)
        await self._fetch_schedule(year)
        await self._fetch_drivers(year)
        await self._fetch_constructors(year)
        await self._fetch_driver_standings(year)
        await self._fetch_constructor_standings(year)

        # Fetch results for all completed rounds
        schedule = self.get_schedule(year)
        now = datetime.now(timezone.utc).date()
        for race in schedule:
            try:
                race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                if race_date < now:
                    round_num = race["round"]
                    # Only fetch if not already permanently cached
                    if not self._cache.get(f"race_result:{year}:{round_num}"):
                        await self._fetch_race_result(year, round_num)
                        # Small delay to be nice to rate limits
                        await asyncio.sleep(0.3)
            except (KeyError, ValueError):
                continue

        logger.info(f"Full cache load complete for {year}")

    async def _periodic_refresh(self, year: int):
        """Background task: refresh volatile data every 30 minutes."""
        while True:
            await asyncio.sleep(1800)  # 30 minutes
            try:
                logger.info(f"Periodic cache refresh for {year}")
                await self._fetch_driver_standings(year)
                await self._fetch_constructor_standings(year)
                # Check for any newly completed races
                await self._check_new_results(year)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Periodic refresh error: {e}")

    async def _check_new_results(self, year: int):
        """Fetch results for any newly completed race not yet cached."""
        schedule = self.get_schedule(year)
        now = datetime.now(timezone.utc).date()
        for race in schedule:
            try:
                race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                if race_date < now:
                    round_num = race["round"]
                    if not self._cache.get(f"race_result:{year}:{round_num}"):
                        await self._fetch_race_result(year, round_num)
                        await asyncio.sleep(0.3)
            except (KeyError, ValueError):
                continue


# Singleton instance
cache_manager = CacheManager()
