"""
Two-tier F1 data cache: in-memory dict → aiosqlite → Jolpica API.
CacheService is created once in lifespan and shared via app.state.
"""
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiosqlite

from ..core.ratings_engine import recompute as _recompute_ratings

logger = logging.getLogger(__name__)

TTL_PERMANENT = 0
TTL_STANDINGS = 300       # 5 min
TTL_SCHEDULE  = 86400     # 24 h
TTL_DRIVERS   = 86400     # 24 h
TTL_WEATHER   = 600       # 10 min


@dataclass
class _Entry:
    data: Any
    fetched_at: datetime
    ttl: int

    @property
    def expired(self) -> bool:
        if self.ttl == 0:
            return False
        return (datetime.now(timezone.utc) - self.fetched_at).total_seconds() > self.ttl


class CacheService:
    """Async-safe two-tier cache. Public getters are synchronous (read from L1).
    Writes go to both L1 (in-memory) and L2 (aiosqlite) asynchronously."""

    def __init__(self, db_path: str, jolpica: Any):
        self._mem: Dict[str, _Entry] = {}
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        self._jolpica = jolpica
        self._loaded_years: set = set()
        self._year_locks: Dict[int, asyncio.Lock] = {}
        self._refresh_task: Optional[asyncio.Task] = None
        self._initialized = False
        self.current_year = datetime.now(timezone.utc).year

    # ── Lifecycle ──────────────────────────────────────────────────

    async def open(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA synchronous=NORMAL")
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key          TEXT PRIMARY KEY,
                data         TEXT NOT NULL,
                fetched_at   TEXT NOT NULL,
                ttl          INTEGER NOT NULL DEFAULT 0
            )
        """)
        await self._db.commit()
        await self._hydrate()

    async def close(self):
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        if self._db:
            await self._db.close()

    async def initialize(self):
        """Fetch fresh data from Jolpica on startup, then start background refresh."""
        try:
            await self._load_year(self.current_year)
            self._initialized = True
            logger.info(f"CacheService initialized for {self.current_year}")
            self._update_fallback_configs(self.current_year)
        except Exception as e:
            if self._loaded_years:
                self._initialized = True
                logger.warning(f"API refresh failed, serving from SQLite: {e}")
            else:
                logger.error(f"Cache init failed (degraded mode): {e}")
        # Load 2025 for driver ratings — use ensure_year (respects SQLite cache,
        # won't re-fetch if already loaded) so we don't trigger 24 API calls on
        # every startup. Isolated try so 2025 failure doesn't affect main-year.
        if self.current_year != 2025:
            try:
                await self.ensure_year(2025)
            except Exception as e:
                logger.warning(f"Could not load 2025 data for driver ratings: {e}")
        # Recompute outside both paths so it runs in happy path AND degraded mode.
        _recompute_ratings(self)
        self._refresh_task = asyncio.create_task(self._periodic_refresh())

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ── Public Sync Getters (read L1) ─────────────────────────────

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
        results = []
        for race in self.get_schedule(year):
            r = self.get_race_result(year, race["round"])
            if r:
                results.append(r)
        return results

    def get_completed_races(self, year: int) -> List[Dict]:
        return [r for r in self.get_schedule(year)
                if self._mem.get(f"race_result:{year}:{r['round']}")]

    def get_next_race(self, year: int) -> Optional[Dict]:
        now = datetime.now(timezone.utc).date()
        for race in self.get_schedule(year):
            try:
                if datetime.strptime(race["date"], "%Y-%m-%d").date() > now:
                    return race
            except (KeyError, ValueError):
                continue
        return None

    def get_upcoming_races(self, year: int) -> List[Dict]:
        now = datetime.now(timezone.utc).date()
        return [r for r in self.get_schedule(year)
                if _safe_date(r.get("date", "")) > now]

    def get_latest_race(self, year: int) -> Optional[Dict]:
        results = self.get_all_race_results(year)
        return results[-1] if results else None

    def get_driver_code_map(self, year: int) -> Dict[str, str]:
        return {d["code"]: d["name"] for d in self.get_drivers(year) if d.get("code")}

    def get_driver_standings_map(self, year: int) -> Dict[str, Dict]:
        """Return {driver_code: standing_dict} for quick lookup."""
        return {s["driver"]: s for s in self.get_driver_standings(year) if s.get("driver")}

    def get_constructor_standings_map(self, year: int) -> Dict[str, Dict]:
        """Return {team_name: standing_dict} for quick lookup."""
        return {s["team_name"]: s for s in self.get_constructor_standings(year) if s.get("team_name")}

    def get_season_stats(self, year: int) -> Dict:
        schedule = self.get_schedule(year)
        completed = self.get_completed_races(year)
        return {
            "total_races": len(schedule),
            "completed_races": len(completed),
            "remaining_races": len(schedule) - len(completed),
        }

    def get_race_summaries(self, year: int) -> List[Dict]:
        summaries = []
        for rr in self.get_all_race_results(year):
            podium = [
                {"position": d["position"], "driver": d["code"],
                 "name": d["name"], "team": d["team"]}
                for d in rr.get("results", [])[:3]
            ]
            summaries.append({
                "race_name": rr.get("raceName", ""),
                "round": rr.get("round", 0),
                "date": rr.get("date", ""),
                "location": rr.get("location", ""),
                "podium": podium,
            })
        return summaries

    def get_performance_trends(self, year: int, limit: int = 5) -> List[Dict]:
        results = self.get_all_race_results(year)
        if not results:
            return []
        if limit:
            results = results[-limit:]
        trends = []
        for rr in results:
            row = {"race": rr.get("raceName", "").replace(" Grand Prix", "").strip()}
            for dr in rr.get("results", []):
                if dr.get("code"):
                    row[dr["code"]] = dr.get("points", 0)
            trends.append(row)
        return trends

    def get_points_breakdown(self, year: int) -> Dict[str, Dict]:
        pts: Dict[str, Dict] = {}
        for rr in self.get_all_race_results(year):
            rnd = rr.get("round", 0)
            for dr in rr.get("results", []):
                code = dr.get("code", "")
                p = dr.get("points", 0)
                if not code:
                    continue
                if code not in pts:
                    pts[code] = {"total": 0, "per_round": {}}
                pts[code]["total"] += p
                pts[code]["per_round"][rnd] = p
        return pts

    # ── On-demand year loading ─────────────────────────────────────

    async def ensure_year(self, year: int):
        if year in self._loaded_years:
            return
        if year not in self._year_locks:
            self._year_locks[year] = asyncio.Lock()
        async with self._year_locks[year]:
            if year not in self._loaded_years:
                await self._load_year(year)

    # ── Private helpers ───────────────────────────────────────────

    def _get(self, key: str, default: Any) -> Any:
        entry = self._mem.get(key)
        return entry.data if entry else default

    async def _put(self, key: str, data: Any, ttl: int):
        now = datetime.now(timezone.utc)
        self._mem[key] = _Entry(data=data, fetched_at=now, ttl=ttl)
        if self._db:
            await self._db.execute(
                "INSERT OR REPLACE INTO cache_entries VALUES (?,?,?,?)",
                (key, json.dumps(data), now.isoformat(), ttl),
            )
            await self._db.commit()

    async def _hydrate(self):
        if not self._db:
            return
        async with self._db.execute(
            "SELECT key, data, fetched_at, ttl FROM cache_entries"
        ) as cur:
            rows = await cur.fetchall()
        loaded = 0
        for key, raw, fetched_at_str, ttl in rows:
            entry = _Entry(
                data=json.loads(raw),
                fetched_at=datetime.fromisoformat(fetched_at_str),
                ttl=ttl,
            )
            if ttl == 0 or not entry.expired:
                self._mem[key] = entry
                loaded += 1
                parts = key.split(":")
                if len(parts) >= 2 and parts[1].isdigit():
                    self._loaded_years.add(int(parts[1]))
        logger.info(f"Hydrated {loaded} cache entries from SQLite")

    async def _load_year(self, year: int):
        j = self._jolpica

        # Fetch metadata concurrently — only if missing or expired
        async def _fetch_if_stale(key: str, fetcher, ttl: int):
            if not self._mem.get(key) or self._mem[key].expired:
                data = await fetcher()
                if data:
                    await self._put(key, data, ttl)

        await asyncio.gather(
            _fetch_if_stale(f"schedule:{year}",     lambda: j.get_schedule(year),     TTL_SCHEDULE),
            _fetch_if_stale(f"drivers:{year}",      lambda: j.get_drivers(year),      TTL_DRIVERS),
            _fetch_if_stale(f"constructors:{year}", lambda: j.get_constructors(year), TTL_DRIVERS),
        )

        # Standings always refresh — fetch concurrently
        drv_data, con_data = await asyncio.gather(
            j.get_driver_standings(year),
            j.get_constructor_standings(year),
        )
        if drv_data:
            await self._put(f"driver_standings:{year}", drv_data, TTL_STANDINGS)
        if con_data:
            await self._put(f"constructor_standings:{year}", con_data, TTL_STANDINGS)

        await self._fetch_missing_results(year)
        self._loaded_years.add(year)
        logger.info(f"Loaded year {year} into cache")

    async def _periodic_refresh(self):
        while True:
            await asyncio.sleep(1800)
            try:
                year = self.current_year
                drv_data, con_data = await asyncio.gather(
                    self._jolpica.get_driver_standings(year),
                    self._jolpica.get_constructor_standings(year),
                )
                if drv_data:
                    await self._put(f"driver_standings:{year}", drv_data, TTL_STANDINGS)
                if con_data:
                    await self._put(f"constructor_standings:{year}", con_data, TTL_STANDINGS)
                await self._fetch_missing_results(year)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Periodic refresh error: {e}")
            # Recompute outside the try — always runs even if data fetch partially failed.
            # recompute() catches and logs its own failures, so this never raises.
            _recompute_ratings(self)

    async def _fetch_missing_results(self, year: int):
        now = datetime.now(timezone.utc).date()
        for race in self.get_schedule(year):
            rnd = race.get("round")
            if _safe_date(race.get("date", "")) < now and not self._mem.get(f"race_result:{year}:{rnd}"):
                result = await self._jolpica.get_race_result(year, rnd)
                if result:
                    await self._put(f"race_result:{year}:{rnd}", result, TTL_PERMANENT)
                await asyncio.sleep(0.3)

    def _update_fallback_configs(self, year: int):
        """Sync live API data back to JSON fallback config files."""
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
        drivers = self.get_drivers(year)
        constructors = self.get_constructors(year)
        if not drivers:
            return

        standings_team = {
            s["driver"]: s["team"]
            for s in self.get_driver_standings(year)
        }

        # -- roster --
        roster_path = os.path.join(config_dir, "fallback_driver_roster.json")
        try:
            with open(roster_path) as f:
                roster_data = json.load(f)
        except Exception:
            roster_data = {}
        existing = roster_data.get("drivers", {})
        new_roster = {}
        for d in drivers:
            code = d.get("code")
            if not code:
                continue
            num_str = str(d.get("number", ""))
            new_roster[code] = {
                "name": d.get("name", ""),
                "team": standings_team.get(code) or existing.get(code, {}).get("team", "Unknown"),
                "number": int(num_str) if num_str.isdigit() else 0,
            }
        roster_data["_comment"] = f"Auto-updated from Jolpica for {year}. Do not edit manually."
        roster_data["drivers"] = new_roster
        with open(roster_path, "w") as f:
            json.dump(roster_data, f, indent=2, ensure_ascii=False)

        # -- driver ratings (add new, keep existing) --
        ratings_path = os.path.join(config_dir, "fallback_driver_ratings.json")
        try:
            with open(ratings_path) as f:
                ratings_data = json.load(f)
        except Exception:
            ratings_data = {}
        default = ratings_data.get("default", {"overall_skill": 0.70, "wet_skill": 0.68, "race_craft": 0.68, "strategy_execution": 0.68})
        dr_ratings = ratings_data.get("drivers", {})
        for d in drivers:
            name = d.get("name", "")
            if name and name not in dr_ratings:
                dr_ratings[name] = default.copy()
        ratings_data["drivers"] = dr_ratings
        with open(ratings_path, "w") as f:
            json.dump(ratings_data, f, indent=2, ensure_ascii=False)

        # -- team ratings (add new, keep existing) --
        team_path = os.path.join(config_dir, "fallback_team_ratings.json")
        try:
            with open(team_path) as f:
                team_data = json.load(f)
        except Exception:
            team_data = {}
        default_team = team_data.get("default", {"dry_pace": 0.70, "wet_pace": 0.70, "strategy": 0.70, "reliability": 0.75})
        teams = team_data.get("teams", {})
        for c in constructors:
            name = c.get("name", "")
            if name and name not in teams:
                teams[name] = default_team.copy()
        team_data["teams"] = teams
        with open(team_path, "w") as f:
            json.dump(team_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Fallback configs updated ({len(new_roster)} drivers, {len(constructors)} teams)")


def _safe_date(date_str: str):
    from datetime import date
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.min.date()
