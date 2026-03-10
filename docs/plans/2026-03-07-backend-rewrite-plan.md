# Backend Rewrite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the 1,253-line monolith with a clean, fully async FastAPI app using DI, aiosqlite, and a live-data ratings engine instead of stale ML pickle models.

**Architecture:** App factory with lifespan context manager. All services live on `app.state` and are injected via `Depends()`. Cache is two-tier (in-memory dict → aiosqlite). FastF1 calls run in a thread pool executor. Prediction uses a ratings engine + Monte Carlo simulation (1000 iterations).

**Tech Stack:** FastAPI, aiosqlite, aiohttp, pydantic-settings, pydantic v2, numpy, fastf1 (thread pool only), google-generativeai (optional)

---

## Directory Target

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── deps.py
│   ├── core/
│   │   ├── f1_ratings.py
│   │   └── monte_carlo.py
│   ├── models/
│   │   ├── common.py
│   │   ├── predict.py
│   │   ├── telemetry.py
│   │   └── strategy.py
│   ├── routers/
│   │   ├── meta.py
│   │   ├── predict.py
│   │   ├── results.py
│   │   ├── telemetry.py
│   │   ├── strategy.py
│   │   └── weather.py
│   └── services/
│       ├── cache.py
│       ├── jolpica.py
│       ├── prediction.py
│       ├── telemetry.py
│       ├── strategy.py
│       ├── weather.py
│       └── results.py
├── config/          (unchanged)
├── data/            (unchanged)
├── main.py          (thin uvicorn entry point)
└── requirements.txt (slimmed down)
```

---

## Task 1: App Skeleton — Config, Error Handling, App Factory

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/models/common.py`
- Create: `backend/app/main.py`

**Step 1: Create the package init**

```python
# backend/app/__init__.py
# empty
```

**Step 2: Create config.py**

```python
# backend/app/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openweather_api_key: str = ""
    google_api_key: str = ""
    jolpica_base: str = "https://api.jolpi.ca/ergast/f1"
    cache_db_path: str = ""          # default resolved at runtime
    fastf1_cache_dir: str = ""       # default resolved at runtime
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def resolved_cache_db(self) -> str:
        if self.cache_db_path:
            return self.cache_db_path
        return os.path.join(os.path.dirname(__file__), "..", "data", "cache.db")

    def resolved_fastf1_dir(self) -> str:
        if self.fastf1_cache_dir:
            return self.fastf1_cache_dir
        return os.path.join(os.path.dirname(__file__), "..", "cache")

settings = Settings()
```

**Step 3: Create models/common.py**

```python
# backend/app/models/common.py
from pydantic import BaseModel
from typing import Any, Optional

class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[Any] = None

class AppError(Exception):
    def __init__(self, error: str, message: str, status_code: int = 400, detail: Any = None):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)

class HealthResponse(BaseModel):
    status: str
    cache_initialized: bool
    year: int
```

**Step 4: Create app/main.py**

```python
# backend/app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models.common import AppError, ErrorResponse, HealthResponse
from .services.cache import CacheService
from .services.jolpica import JolpicaClient

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──────────────────────────────────────────────────
    jolpica = JolpicaClient(base_url=settings.jolpica_base)
    await jolpica.open()
    app.state.jolpica = jolpica

    cache = CacheService(
        db_path=settings.resolved_cache_db(),
        jolpica=jolpica,
    )
    await cache.open()
    await cache.initialize()
    app.state.cache = cache

    logger.info("F1 backend ready")
    yield

    # ── shutdown ─────────────────────────────────────────────────
    await cache.close()
    await jolpica.close()
    logger.info("F1 backend shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="F1 Insight Hub API",
        version="4.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.error,
                message=exc.message,
                detail=exc.detail,
            ).model_dump(),
        )

    @app.get("/health", response_model=HealthResponse)
    async def health(request: Request):
        cache: CacheService = request.app.state.cache
        return HealthResponse(
            status="ok",
            cache_initialized=cache.is_initialized,
            year=cache.current_year,
        )

    # Routers registered in Task 6–11
    from .routers import meta, predict, results, telemetry, strategy, weather
    app.include_router(meta.router, prefix="/api/meta")
    app.include_router(predict.router, prefix="/api/predict")
    app.include_router(results.router, prefix="/api/results")
    app.include_router(telemetry.router, prefix="/api/telemetry")
    app.include_router(strategy.router, prefix="/api/strategy")
    app.include_router(weather.router, prefix="/api/weather")

    return app

app = create_app()
```

**Step 5: Verify imports compile**

```bash
cd backend && python -c "from app.config import settings; print(settings.jolpica_base)"
```

Expected: `https://api.jolpi.ca/ergast/f1`

**Step 6: Commit**

```bash
git add backend/app/
git commit -m "feat: add app skeleton — config, error handling, lifespan factory"
```

---

## Task 2: Async Cache Service

Port `services/cache_manager.py` to fully async aiosqlite.

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/cache.py`

**Step 1: Install aiosqlite (add to requirements first — see Task 12)**

For now, verify it's available:
```bash
pip show aiosqlite 2>/dev/null || pip install aiosqlite
```

**Step 2: Write cache.py**

```python
# backend/app/services/cache.py
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
        # Only fetch metadata if missing or expired
        if not self._mem.get(f"schedule:{year}") or self._mem[f"schedule:{year}"].expired:
            data = await j.get_schedule(year)
            if data:
                await self._put(f"schedule:{year}", data, TTL_SCHEDULE)
        if not self._mem.get(f"drivers:{year}") or self._mem[f"drivers:{year}"].expired:
            data = await j.get_drivers(year)
            if data:
                await self._put(f"drivers:{year}", data, TTL_DRIVERS)
        if not self._mem.get(f"constructors:{year}") or self._mem[f"constructors:{year}"].expired:
            data = await j.get_constructors(year)
            if data:
                await self._put(f"constructors:{year}", data, TTL_DRIVERS)

        # Standings always refresh
        data = await j.get_driver_standings(year)
        if data:
            await self._put(f"driver_standings:{year}", data, TTL_STANDINGS)
        data = await j.get_constructor_standings(year)
        if data:
            await self._put(f"constructor_standings:{year}", data, TTL_STANDINGS)

        # Race results (permanent once cached)
        schedule = self.get_schedule(year)
        now = datetime.now(timezone.utc).date()
        for race in schedule:
            rnd = race.get("round")
            rdate = _safe_date(race.get("date", ""))
            if rdate < now and not self._mem.get(f"race_result:{year}:{rnd}"):
                result = await j.get_race_result(year, rnd)
                if result:
                    await self._put(f"race_result:{year}:{rnd}", result, TTL_PERMANENT)
                await asyncio.sleep(0.3)

        self._loaded_years.add(year)
        logger.info(f"Loaded year {year} into cache")

    async def _periodic_refresh(self):
        while True:
            await asyncio.sleep(1800)
            try:
                j = self._jolpica
                year = self.current_year
                data = await j.get_driver_standings(year)
                if data:
                    await self._put(f"driver_standings:{year}", data, TTL_STANDINGS)
                data = await j.get_constructor_standings(year)
                if data:
                    await self._put(f"constructor_standings:{year}", data, TTL_STANDINGS)
                await self._load_new_results(year)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Periodic refresh error: {e}")

    async def _load_new_results(self, year: int):
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
```

**Step 3: Verify it imports**

```bash
cd backend && python -c "from app.services.cache import CacheService; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/services/
git commit -m "feat: async CacheService with aiosqlite and fallback config sync"
```

---

## Task 3: Jolpica API Client

Extract all Jolpica fetch logic from `services/cache_manager.py` into a standalone async client.

**Files:**
- Create: `backend/app/services/jolpica.py`

**Step 1: Write jolpica.py**

```python
# backend/app/services/jolpica.py
"""Async Jolpica-F1 API client. One shared aiohttp session for the app lifetime."""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class JolpicaClient:
    def __init__(self, base_url: str = "https://api.jolpi.ca/ergast/f1"):
        self._base = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def open(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Accept": "application/json"},
        )

    async def close(self):
        if self._session:
            await self._session.close()

    # ── Low-level GET ──────────────────────────────────────────────

    async def _get(self, path: str) -> Optional[Dict]:
        if not self._session:
            return None
        url = f"{self._base}/{path}"
        try:
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
                if resp.status == 429:
                    logger.warning(f"Rate limited on {path}, backing off 5s")
                    await asyncio.sleep(5)
                    return None
                logger.warning(f"Jolpica {path} → HTTP {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Jolpica fetch error [{path}]: {e}")
            return None

    # ── Domain fetch methods ──────────────────────────────────────

    async def get_schedule(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}.json")
        if not data:
            return []
        try:
            races_raw = data["MRData"]["RaceTable"]["Races"]
            return [
                {
                    "round": int(r["round"]),
                    "race_name": r["raceName"],
                    "date": r["date"],
                    "circuit": r["Circuit"]["circuitName"],
                    "location": r["Circuit"]["Location"].get("locality", ""),
                    "country": r["Circuit"]["Location"].get("country", ""),
                }
                for r in races_raw
            ]
        except (KeyError, TypeError) as e:
            logger.error(f"parse schedule {year}: {e}")
            return []

    async def get_drivers(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/drivers.json?limit=30")
        if not data:
            return []
        try:
            return [
                {
                    "id": d.get("driverId", ""),
                    "code": d.get("code", ""),
                    "name": f"{d.get('givenName', '')} {d.get('familyName', '')}".strip(),
                    "number": d.get("permanentNumber", ""),
                    "nationality": d.get("nationality", ""),
                }
                for d in data["MRData"]["DriverTable"]["Drivers"]
            ]
        except (KeyError, TypeError) as e:
            logger.error(f"parse drivers {year}: {e}")
            return []

    async def get_constructors(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/constructors.json")
        if not data:
            return []
        try:
            return [
                {
                    "id": c.get("constructorId", ""),
                    "name": c.get("name", ""),
                    "nationality": c.get("nationality", ""),
                }
                for c in data["MRData"]["ConstructorTable"]["Constructors"]
            ]
        except (KeyError, TypeError) as e:
            logger.error(f"parse constructors {year}: {e}")
            return []

    async def get_driver_standings(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/driverStandings.json")
        if not data:
            return []
        try:
            lists = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not lists:
                return []
            return [
                {
                    "position": int(s["position"]),
                    "driver": s["Driver"].get("code", ""),
                    "name": f"{s['Driver'].get('givenName','')} {s['Driver'].get('familyName','')}".strip(),
                    "team": s["Constructors"][0]["name"] if s.get("Constructors") else "Unknown",
                    "points": float(s["points"]),
                    "wins": int(s["wins"]),
                }
                for s in lists[0]["DriverStandings"]
            ]
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"parse driver standings {year}: {e}")
            return []

    async def get_constructor_standings(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/constructorStandings.json")
        if not data:
            return []
        try:
            lists = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not lists:
                return []
            return [
                {
                    "position": int(s["position"]),
                    "team_name": s["Constructor"].get("name", ""),
                    "points": float(s["points"]),
                    "wins": int(s["wins"]),
                }
                for s in lists[0]["ConstructorStandings"]
            ]
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"parse constructor standings {year}: {e}")
            return []

    async def get_race_result(self, year: int, round_num: int) -> Optional[Dict]:
        data = await self._get(f"{year}/{round_num}/results.json")
        if not data:
            return None
        try:
            races = data["MRData"]["RaceTable"]["Races"]
            if not races:
                return None
            race = races[0]
            results = []
            for r in race.get("Results", []):
                time_str = (r.get("Time") or {}).get("time", "") if isinstance(r.get("Time"), dict) else ""
                results.append({
                    "position": int(r["position"]),
                    "code": r["Driver"].get("code", ""),
                    "name": f"{r['Driver'].get('givenName','')} {r['Driver'].get('familyName','')}".strip(),
                    "team": r["Constructor"].get("name", ""),
                    "points": float(r.get("points", 0)),
                    "time": time_str,
                    "status": r.get("status", ""),
                    "laps": int(r.get("laps", 0)),
                    "grid": int(r.get("grid", 0)),
                })
            fastest = next(
                ({"driver": r["Driver"].get("code",""), "time": (r["FastestLap"]["Time"]["time"] if r.get("FastestLap") else ""), "lap": r.get("FastestLap", {}).get("lap","")}
                 for r in race.get("Results",[]) if r.get("FastestLap",{}).get("rank") == "1"),
                {}
            )
            return {
                "raceName": race.get("raceName", ""),
                "round": int(race.get("round", round_num)),
                "date": race.get("date", ""),
                "location": race.get("Circuit", {}).get("Location", {}).get("locality", ""),
                "results": results,
                "fastestLap": fastest,
            }
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"parse race result {year}/{round_num}: {e}")
            return None
```

**Step 2: Verify**

```bash
cd backend && python -c "from app.services.jolpica import JolpicaClient; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/app/services/jolpica.py
git commit -m "feat: async JolpicaClient — extracted from cache_manager"
```

---

## Task 4: Ratings Engine

Replace the stale ML pickles with a live-data-backed driver scoring formula.

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/f1_ratings.py`

**Step 1: Write f1_ratings.py**

```python
# backend/app/core/f1_ratings.py
"""
Dynamic F1 driver and team ratings engine.
Combines JSON config ratings with live Jolpica standings data.
"""
import json
import logging
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config")

# Weights for the form_factor calculation from standings points
_MAX_EXPECTED_POINTS = 200.0   # rough upper bound mid-season
_WEATHER_PROFILES: Dict[str, Dict[str, float]] = {
    # driver_name -> {dry, wet}  (override table for known wet-weather specialists)
    "Max Verstappen":    {"dry": 1.00, "wet": 1.05},
    "Lewis Hamilton":    {"dry": 0.97, "wet": 1.06},
    "George Russell":    {"dry": 0.95, "wet": 1.02},
    "Fernando Alonso":   {"dry": 0.93, "wet": 1.04},
    "Lando Norris":      {"dry": 0.98, "wet": 1.01},
    "Pierre Gasly":      {"dry": 0.88, "wet": 1.00},
}
_DEFAULT_WEATHER = {"dry": 1.0, "wet": 0.95}


def _load_json(filename: str) -> Dict:
    path = os.path.join(CONFIG_DIR, filename)
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {filename}: {e}")
        return {}


def _load_driver_ratings() -> Dict[str, Dict]:
    data = _load_json("fallback_driver_ratings.json")
    return data.get("drivers", {})


def _load_team_ratings() -> Dict[str, Dict]:
    data = _load_json("fallback_team_ratings.json")
    return data.get("teams", {})


def _load_track_characteristics() -> Dict[str, Dict]:
    return _load_json("track_characteristics.json")


def _find_team_rating(team_name: str, team_ratings: Dict[str, Dict]) -> Dict:
    """Fuzzy match team name against ratings keys."""
    default = {"dry_pace": 0.70, "wet_pace": 0.70, "strategy": 0.70, "reliability": 0.75}
    if team_name in team_ratings:
        return team_ratings[team_name]
    # partial match
    for key, val in team_ratings.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return val
    return default


def compute_driver_scores(
    driver_code_to_name: Dict[str, str],
    driver_standings: Dict[str, Dict],   # {code: {points, position, team, wins}}
    constructor_standings: Dict[str, Dict],  # {team_name: {points, position}}
    track_name: str = "",
    weather: str = "dry",                 # "dry" | "wet" | "mixed"
) -> Dict[str, float]:
    """
    Return {driver_code: score} where score is a 0–1 float
    representing overall predicted performance strength.

    Formula:
      score = base_skill × team_mult × form_factor × weather_mod
    """
    dr_ratings = _load_driver_ratings()
    team_ratings = _load_team_ratings()
    track_chars = _load_track_characteristics()

    is_wet = weather.lower() in ("wet", "heavy rain", "light rain", "rain")
    is_mixed = weather.lower() in ("mixed", "variable")

    # Normalise constructor points to 0–1
    max_constructor_pts = max(
        (s.get("points", 0) for s in constructor_standings.values()), default=1
    ) or 1
    max_driver_pts = max(
        (s.get("points", 0) for s in driver_standings.values()), default=1
    ) or 1

    scores: Dict[str, float] = {}

    for code, name in driver_code_to_name.items():
        # Base skill from config (default 0.70)
        dr_cfg = dr_ratings.get(name, {})
        if is_wet:
            base = dr_cfg.get("wet_skill", dr_cfg.get("overall_skill", 0.70))
        else:
            base = dr_cfg.get("overall_skill", 0.70)

        # Team performance multiplier from constructor standings
        standing = driver_standings.get(code, {})
        team = standing.get("team", "Unknown")
        con_standing = constructor_standings.get(team, {})
        con_pts = con_standing.get("points", 0)
        team_mult = 0.8 + 0.2 * (con_pts / max_constructor_pts)  # 0.8–1.0 range

        # Form factor from driver standings points (0.85–1.0 range)
        dr_pts = standing.get("points", 0)
        form = 0.85 + 0.15 * (dr_pts / max_driver_pts)

        # Weather modifier
        weather_profile = _WEATHER_PROFILES.get(name, _DEFAULT_WEATHER)
        if is_wet:
            weather_mod = weather_profile["wet"]
        elif is_mixed:
            weather_mod = (weather_profile["dry"] + weather_profile["wet"]) / 2
        else:
            weather_mod = weather_profile["dry"]

        # Track affinity (optional — track_chars may define per-driver affinities)
        track_mod = 1.0
        if track_name and track_name in track_chars:
            affinity = track_chars[track_name].get("driver_affinity", {})
            track_mod = affinity.get(code, affinity.get(name, 1.0))

        score = base * team_mult * form * weather_mod * track_mod
        scores[code] = min(score, 1.0)

    return scores
```

**Step 2: Verify**

```bash
cd backend && python -c "from app.core.f1_ratings import compute_driver_scores; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/app/core/
git commit -m "feat: dynamic ratings engine — base_skill × team × form × weather × track"
```

---

## Task 5: Monte Carlo Race Simulator

**Files:**
- Create: `backend/app/core/monte_carlo.py`

**Step 1: Write monte_carlo.py**

```python
# backend/app/core/monte_carlo.py
"""
Monte Carlo race outcome simulator.
Takes driver scores (0–1) and runs N iterations to produce
probability distributions over finishing positions.
"""
import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)

F1_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def simulate_race(
    driver_scores: Dict[str, float],
    n_iterations: int = 1000,
    chaos_factor: float = 0.15,   # std deviation of Gaussian noise
) -> List[Dict]:
    """
    Simulate a race grid n_iterations times.

    Returns a list of dicts sorted by median finishing position:
      [{"driver": code, "win_pct": 0.23, "podium_pct": 0.61,
        "points_pct": 0.80, "median_pos": 2, "expected_points": 14.1}, ...]
    """
    if not driver_scores:
        return []

    codes = list(driver_scores.keys())
    base = np.array([driver_scores[c] for c in codes], dtype=float)
    n = len(codes)

    # (n_iterations × n_drivers) score matrix with Gaussian noise
    noise = np.random.normal(0, chaos_factor, size=(n_iterations, n))
    scores_matrix = base[np.newaxis, :] + noise          # broadcast
    scores_matrix = np.clip(scores_matrix, 0.01, None)   # no negatives

    # Sort descending each row → finishing order (0 = P1)
    order_matrix = np.argsort(-scores_matrix, axis=1)    # (iters, n)

    # Tally results
    wins     = np.zeros(n, dtype=int)
    podiums  = np.zeros(n, dtype=int)
    in_pts   = np.zeros(n, dtype=int)
    pos_sum  = np.zeros(n, dtype=int)
    pts_sum  = np.zeros(n, dtype=float)
    # Inverse permutation: pos_rows[iter, driver] = finishing position (0-indexed)
    # np.argsort on order_matrix gives the rank of each driver per iteration.
    # NOTE: the original loop-based approach in this plan was buggy (incorrect fancy
    # indexing). argsort(order_matrix, axis=1) is the correct vectorised fix.
    pos_rows = np.argsort(order_matrix, axis=1)

    for iter_i in range(n_iterations):
        for driver_i, pos in enumerate(pos_rows[iter_i]):
            pos_1based = pos + 1
            pos_sum[driver_i] += pos_1based
            if pos == 0:
                wins[driver_i] += 1
            if pos < 3:
                podiums[driver_i] += 1
            if pos < 10:
                in_pts[driver_i] += 1
                pts_sum[driver_i] += F1_POINTS[pos]

    results = []
    for i, code in enumerate(codes):
        results.append({
            "driver": code,
            "win_pct":      round(wins[i] / n_iterations, 4),
            "podium_pct":   round(podiums[i] / n_iterations, 4),
            "points_pct":   round(in_pts[i] / n_iterations, 4),
            "median_pos":   int(round(pos_sum[i] / n_iterations)),
            "expected_pts": round(pts_sum[i] / n_iterations, 2),
        })

    results.sort(key=lambda x: x["median_pos"])
    for rank, r in enumerate(results, 1):
        r["predicted_position"] = rank

    return results
```

**Step 2: Quick smoke test**

```bash
cd backend && python -c "
from app.core.monte_carlo import simulate_race
scores = {'VER': 0.92, 'NOR': 0.88, 'HAM': 0.85, 'RUS': 0.82}
out = simulate_race(scores, n_iterations=200)
for r in out: print(r)
"
```

Expected: sorted list with VER having highest win_pct.

**Step 3: Commit**

```bash
git add backend/app/core/monte_carlo.py
git commit -m "feat: Monte Carlo race simulator — 1000 iterations, numpy vectorised"
```

---

## Task 6: Prediction Service + Router

**Files:**
- Create: `backend/app/services/prediction.py`
- Create: `backend/app/models/predict.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/predict.py`

**Step 1: Write models/predict.py**

```python
# backend/app/models/predict.py
from pydantic import BaseModel, Field
from typing import List, Optional

class DriverPredictRequest(BaseModel):
    driver: str = Field(..., description="3-letter driver code, e.g. VER")
    track: str = Field(..., description="Race name, e.g. 'Monaco Grand Prix'")
    weather: str = Field(default="dry", description="dry | wet | mixed")
    year: Optional[int] = None

class DriverPrediction(BaseModel):
    driver: str
    name: str
    team: str
    predicted_position: int
    win_probability: float
    podium_probability: float
    expected_points: float
    key_factors: List[str]

class RacePredictRequest(BaseModel):
    track: str
    weather: str = "dry"
    year: Optional[int] = None

class RaceGridEntry(BaseModel):
    position: int
    driver: str
    name: str
    team: str
    win_probability: float
    podium_probability: float
    expected_points: float

class RaceGridPrediction(BaseModel):
    track: str
    weather: str
    year: int
    grid: List[RaceGridEntry]
```

**Step 2: Write services/prediction.py**

```python
# backend/app/services/prediction.py
"""
Prediction service — ties together ratings engine + Monte Carlo simulator.
Runs CPU-bound simulation in thread pool to avoid blocking the event loop.
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..core.f1_ratings import compute_driver_scores
from ..core.monte_carlo import simulate_race
from ..models.predict import DriverPrediction, RaceGridEntry

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mc_")


class PredictionService:
    def __init__(self, cache):
        self._cache = cache

    def _current_year(self, year: Optional[int] = None) -> int:
        return year or datetime.now(timezone.utc).year

    async def predict_race_grid(
        self, track: str, weather: str = "dry", year: Optional[int] = None
    ) -> List[RaceGridEntry]:
        y = self._current_year(year)
        cache = self._cache

        await cache.ensure_year(y)

        code_to_name = cache.get_driver_code_map(y)
        driver_standings = cache.get_driver_standings_map(y)
        constructor_standings = cache.get_constructor_standings_map(y)

        if not code_to_name:
            code_to_name = _fallback_driver_map()

        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            _executor,
            compute_driver_scores,
            code_to_name, driver_standings, constructor_standings, track, weather,
        )
        results = await loop.run_in_executor(
            _executor, simulate_race, scores, 1000,
        )

        name_map = code_to_name
        team_map = {s["driver"]: s["team"] for s in cache.get_driver_standings(y)}

        return [
            RaceGridEntry(
                position=r["predicted_position"],
                driver=r["driver"],
                name=name_map.get(r["driver"], r["driver"]),
                team=team_map.get(r["driver"], "Unknown"),
                win_probability=r["win_pct"],
                podium_probability=r["podium_pct"],
                expected_points=r["expected_pts"],
            )
            for r in results
        ]

    async def predict_driver(
        self, driver_code: str, track: str, weather: str = "dry", year: Optional[int] = None
    ) -> Optional[DriverPrediction]:
        grid = await self.predict_race_grid(track, weather, year)
        y = self._current_year(year)
        name_map = self._cache.get_driver_code_map(y)
        team_map = {s["driver"]: s["team"] for s in self._cache.get_driver_standings(y)}

        entry = next((e for e in grid if e.driver == driver_code), None)
        if not entry:
            return None

        key_factors = _build_key_factors(driver_code, weather, entry)
        return DriverPrediction(
            driver=driver_code,
            name=name_map.get(driver_code, driver_code),
            team=team_map.get(driver_code, "Unknown"),
            predicted_position=entry.position,
            win_probability=entry.win_probability,
            podium_probability=entry.podium_probability,
            expected_points=entry.expected_points,
            key_factors=key_factors,
        )


def _build_key_factors(code: str, weather: str, entry: RaceGridEntry) -> List[str]:
    factors = []
    if entry.win_probability > 0.3:
        factors.append("High win probability based on current championship form")
    if weather.lower() in ("wet", "rain", "heavy rain"):
        factors.append("Wet conditions add variability — wet-weather skill is a differentiator")
    if entry.position <= 3:
        factors.append("Strong team performance and car pace")
    if entry.position > 10:
        factors.append("Midfield battle — strategy and reliability key")
    return factors or ["Competitive midfield — any result possible"]


def _fallback_driver_map() -> Dict[str, str]:
    import json, os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "fallback_driver_roster.json")
    try:
        with open(path) as f:
            data = json.load(f)
        return {code: d["name"] for code, d in data.get("drivers", {}).items()}
    except Exception:
        return {}
```

**Step 3: Write routers/predict.py**

```python
# backend/app/routers/predict.py
from fastapi import APIRouter, Depends, Request
from ..models.predict import (
    DriverPredictRequest, DriverPrediction,
    RacePredictRequest, RaceGridPrediction,
)
from ..models.common import AppError
from ..deps import get_prediction_service

router = APIRouter(tags=["prediction"])


@router.post("/driver", response_model=DriverPrediction)
async def predict_driver(
    body: DriverPredictRequest,
    svc=Depends(get_prediction_service),
):
    result = await svc.predict_driver(body.driver, body.track, body.weather, body.year)
    if not result:
        raise AppError("DRIVER_NOT_FOUND", f"Driver '{body.driver}' not found", status_code=404)
    return result


@router.post("/race", response_model=RaceGridPrediction)
async def predict_race(
    body: RacePredictRequest,
    request: Request,
    svc=Depends(get_prediction_service),
):
    from datetime import datetime, timezone
    year = body.year or datetime.now(timezone.utc).year
    grid = await svc.predict_race_grid(body.track, body.weather, body.year)
    return RaceGridPrediction(
        track=body.track,
        weather=body.weather,
        year=year,
        grid=grid,
    )
```

**Step 4: Write deps.py**

```python
# backend/app/deps.py
from fastapi import Request
from .services.cache import CacheService
from .services.jolpica import JolpicaClient
from .services.prediction import PredictionService


def get_cache(request: Request) -> CacheService:
    return request.app.state.cache


def get_jolpica(request: Request) -> JolpicaClient:
    return request.app.state.jolpica


def get_prediction_service(request: Request) -> PredictionService:
    return PredictionService(cache=request.app.state.cache)
```

**Step 5: Commit**

```bash
git add backend/app/
git commit -m "feat: prediction service + router — ratings engine + Monte Carlo, no stale pickles"
```

---

## Task 7: Results Service + Router

**Files:**
- Create: `backend/app/services/results.py`
- Create: `backend/app/routers/results.py`

**Step 1: Write services/results.py**

```python
# backend/app/services/results.py
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
```

**Step 2: Write routers/results.py**

```python
# backend/app/routers/results.py
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from ..deps import get_cache
from ..models.common import AppError
from ..services.results import ResultsService

router = APIRouter(tags=["results"])


def _year(request: Request, year: Optional[int] = None) -> int:
    return year or datetime.now(timezone.utc).year


@router.get("/standings")
async def driver_standings(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    await cache.ensure_year(y)
    svc = ResultsService(cache)
    return {"year": y, "standings": svc.get_driver_standings(y)}


@router.get("/constructor-standings")
async def constructor_standings(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    await cache.ensure_year(y)
    svc = ResultsService(cache)
    return {"year": y, "standings": svc.get_constructor_standings(y)}


@router.get("/calendar")
async def calendar(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    await cache.ensure_year(y)
    svc = ResultsService(cache)
    return {"year": y, "calendar": svc.get_calendar(y)}


@router.get("/next-race")
async def next_race(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    svc = ResultsService(cache)
    race = svc.get_next_race(y)
    if not race:
        raise AppError("NO_NEXT_RACE", f"No upcoming races found for {y}", status_code=404)
    return race


@router.get("/recent")
async def recent_races(
    year: Optional[int] = Query(None),
    limit: int = Query(5, ge=1, le=24),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    svc = ResultsService(cache)
    return {"year": y, "races": svc.get_recent_races(y, limit)}


@router.get("/session/{year}/{round}")
async def session_result(
    year: int,
    round: int,
    cache=Depends(get_cache),
):
    await cache.ensure_year(year)
    svc = ResultsService(cache)
    result = svc.get_session_result(year, round)
    if not result:
        raise AppError("RESULT_NOT_FOUND", f"No result for {year} round {round}", status_code=404)
    return result


@router.get("/upcoming")
async def upcoming_races(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    svc = ResultsService(cache)
    return {"year": y, "races": svc.get_upcoming_races(y)}
```

**Step 3: Commit**

```bash
git add backend/app/services/results.py backend/app/routers/results.py
git commit -m "feat: results service + router — standings, calendar, recent races"
```

---

## Task 8: Meta Router

**Files:**
- Create: `backend/app/routers/meta.py`

**Step 1: Write routers/meta.py**

```python
# backend/app/routers/meta.py
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from ..deps import get_cache

router = APIRouter(tags=["meta"])


def _y(year: Optional[int]) -> int:
    return year or datetime.now(timezone.utc).year


@router.get("/drivers/{year}")
async def drivers(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    return {"year": year, "drivers": cache.get_drivers(year)}


@router.get("/drivers")
async def drivers_current(year: Optional[int] = Query(None), cache=Depends(get_cache)):
    y = _y(year)
    await cache.ensure_year(y)
    return {"year": y, "drivers": cache.get_drivers(y)}


@router.get("/constructors/{year}")
async def constructors(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    return {"year": year, "constructors": cache.get_constructors(year)}


@router.get("/constructors")
async def constructors_current(year: Optional[int] = Query(None), cache=Depends(get_cache)):
    y = _y(year)
    await cache.ensure_year(y)
    return {"year": y, "constructors": cache.get_constructors(y)}


@router.get("/schedule/{year}")
async def schedule(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    return {"year": year, "schedule": cache.get_schedule(year)}


@router.get("/tracks/{year}")
async def tracks(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    schedule = cache.get_schedule(year)
    return {"year": year, "tracks": [{"name": r["race_name"], "circuit": r["circuit"], "country": r["country"], "date": r["date"]} for r in schedule]}
```

**Step 2: Commit**

```bash
git add backend/app/routers/meta.py
git commit -m "feat: meta router — drivers, constructors, schedule, tracks"
```

---

## Task 9: Telemetry Service + Router

Port `services/telemetry_analyzer_service.py` — keep all FastF1 logic, wrap in `run_in_executor`.

**Files:**
- Create: `backend/app/services/telemetry.py`
- Create: `backend/app/models/telemetry.py`
- Create: `backend/app/routers/telemetry.py`

**Step 1: Write models/telemetry.py**

```python
# backend/app/models/telemetry.py
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class TelemetryRequest(BaseModel):
    year: int
    race: str
    session: str = "R"      # R | Q | FP1 | FP2 | FP3 | S
    driver: str             # driver code

class DriverComparisonRequest(BaseModel):
    year: int
    race: str
    session: str = "Q"
    driver1: str
    driver2: str

class SpeedTraceRequest(BaseModel):
    year: int
    race: str
    session: str = "Q"
    driver: str
    lap: Optional[int] = None   # None = fastest

class TrackMapRequest(BaseModel):
    year: int
    race: str
    session: str = "Q"
    driver: str
    lap: Optional[int] = None

class WeatherContextRequest(BaseModel):
    year: int
    race: str
    session: str = "R"
```

**Step 2: Write services/telemetry.py**

Port the core methods from `services/telemetry_analyzer_service.py`. Key pattern — every public method is `async`, delegates to a sync `_*` method via `run_in_executor`:

```python
# backend/app/services/telemetry.py
import asyncio
import logging
import os
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="f1tel_")


def _setup_fastf1(cache_dir: str):
    import fastf1
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)


def _clean(data: Any) -> Any:
    """Remove NaN/inf for JSON serialisation."""
    if isinstance(data, (list, tuple)):
        return [_clean(x) for x in data]
    if isinstance(data, dict):
        return {k: _clean(v) for k, v in data.items()}
    if isinstance(data, float) and (np.isnan(data) or np.isinf(data)):
        return None
    if hasattr(data, "item"):       # numpy scalar
        v = data.item()
        return None if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else v
    return data


class TelemetryService:
    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir
        _setup_fastf1(cache_dir)

    def _load_session(self, year: int, race: str, session_type: str):
        import fastf1
        ses = fastf1.get_session(year, race, session_type)
        ses.load(laps=True, telemetry=True, weather=True, messages=False)
        return ses

    # ── analyze ──────────────────────────────────────────────────

    def _analyze(self, year: int, race: str, session_type: str, driver: str) -> Dict:
        ses = self._load_session(year, race, session_type)
        laps = ses.laps.pick_drivers(driver)
        if laps.empty:
            return {"error": f"No laps found for {driver}"}
        fastest = laps.pick_fastest()
        tel = fastest.get_telemetry()
        return _clean({
            "driver": driver,
            "lap_time": str(fastest["LapTime"]),
            "sector_1": str(fastest["Sector1Time"]),
            "sector_2": str(fastest["Sector2Time"]),
            "sector_3": str(fastest["Sector3Time"]),
            "max_speed": float(tel["Speed"].max()),
            "min_speed": float(tel["Speed"].min()),
            "avg_speed": float(tel["Speed"].mean()),
            "full_throttle_pct": float((tel["Throttle"] > 95).mean() * 100),
            "braking_pct": float((tel["Brake"] > 50).mean() * 100),
        })

    async def analyze(self, year: int, race: str, session: str, driver: str) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._analyze, year, race, session, driver)

    # ── speed trace ───────────────────────────────────────────────

    def _speed_trace(self, year: int, race: str, session_type: str, driver: str, lap: Optional[int]) -> Dict:
        ses = self._load_session(year, race, session_type)
        laps = ses.laps.pick_drivers(driver)
        if laps.empty:
            return {"error": f"No laps for {driver}"}
        target = laps.iloc[lap - 1] if lap else laps.pick_fastest()
        tel = target.get_telemetry()
        return _clean({
            "driver": driver,
            "lap_time": str(target["LapTime"]),
            "distance": tel["Distance"].tolist(),
            "speed":    tel["Speed"].tolist(),
            "throttle": tel["Throttle"].tolist(),
            "brake":    tel["Brake"].tolist(),
            "gear":     tel["nGear"].tolist(),
            "drs":      tel["DRS"].tolist() if "DRS" in tel.columns else [],
        })

    async def speed_trace(self, year: int, race: str, session: str, driver: str, lap: Optional[int] = None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._speed_trace, year, race, session, driver, lap)

    # ── driver comparison ─────────────────────────────────────────

    def _compare(self, year: int, race: str, session_type: str, d1: str, d2: str) -> Dict:
        ses = self._load_session(year, race, session_type)
        results = {}
        for drv in (d1, d2):
            laps = ses.laps.pick_drivers(drv)
            if laps.empty:
                results[drv] = {"error": f"No laps for {drv}"}
                continue
            fastest = laps.pick_fastest()
            tel = fastest.get_telemetry()
            results[drv] = _clean({
                "lap_time": str(fastest["LapTime"]),
                "max_speed": float(tel["Speed"].max()),
                "avg_speed": float(tel["Speed"].mean()),
                "full_throttle_pct": float((tel["Throttle"] > 95).mean() * 100),
            })
        return {"driver1": d1, "driver2": d2, "comparison": results}

    async def driver_comparison(self, year: int, race: str, session: str, d1: str, d2: str) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._compare, year, race, session, d1, d2)

    # ── track map ─────────────────────────────────────────────────

    def _track_map(self, year: int, race: str, session_type: str, driver: str, lap: Optional[int]) -> Dict:
        ses = self._load_session(year, race, session_type)
        laps = ses.laps.pick_drivers(driver)
        if laps.empty:
            return {"error": f"No laps for {driver}"}
        target = laps.iloc[lap - 1] if lap else laps.pick_fastest()
        tel = target.get_telemetry().add_distance()
        return _clean({
            "driver": driver,
            "x": tel["X"].tolist(),
            "y": tel["Y"].tolist(),
            "speed": tel["Speed"].tolist(),
            "distance": tel["Distance"].tolist(),
        })

    async def track_map(self, year: int, race: str, session: str, driver: str, lap: Optional[int] = None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._track_map, year, race, session, driver, lap)

    # ── weather context ───────────────────────────────────────────

    def _weather(self, year: int, race: str, session_type: str) -> Dict:
        ses = self._load_session(year, race, session_type)
        w = ses.weather_data
        if w is None or w.empty:
            return {"error": "No weather data available"}
        return _clean({
            "air_temp_mean":   float(w["AirTemp"].mean()),
            "air_temp_min":    float(w["AirTemp"].min()),
            "air_temp_max":    float(w["AirTemp"].max()),
            "track_temp_mean": float(w["TrackTemp"].mean()),
            "humidity_mean":   float(w["Humidity"].mean()),
            "rainfall":        bool(w["Rainfall"].any()),
            "wind_speed_mean": float(w["WindSpeed"].mean()),
            "pressure_mean":   float(w["Pressure"].mean()),
        })

    async def weather_context(self, year: int, race: str, session: str) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._weather, year, race, session)

    # ── available sessions ────────────────────────────────────────

    def _available_sessions(self, year: int) -> List[Dict]:
        import fastf1
        try:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
            sessions = []
            for _, event in schedule.iterrows():
                sessions.append({
                    "round": int(event.get("RoundNumber", 0)),
                    "race_name": str(event.get("EventName", "")),
                    "date": str(event.get("EventDate", ""))[:10],
                    "sessions": ["FP1", "FP2", "FP3", "Q", "R"],
                })
            return sessions
        except Exception as e:
            logger.error(f"Failed to get schedule for {year}: {e}")
            return []

    async def available_sessions(self, year: int) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._available_sessions, year)
```

**Step 3: Write routers/telemetry.py**

```python
# backend/app/routers/telemetry.py
from fastapi import APIRouter, Depends, Request
from ..models.telemetry import (
    TelemetryRequest, DriverComparisonRequest,
    SpeedTraceRequest, TrackMapRequest, WeatherContextRequest,
)
from ..models.common import AppError
from ..deps import get_telemetry_service

router = APIRouter(tags=["telemetry"])


@router.post("/analyze")
async def analyze(body: TelemetryRequest, svc=Depends(get_telemetry_service)):
    result = await svc.analyze(body.year, body.race, body.session, body.driver)
    if "error" in result:
        raise AppError("TELEMETRY_ERROR", result["error"], status_code=404)
    return result


@router.post("/speed-trace")
async def speed_trace(body: SpeedTraceRequest, svc=Depends(get_telemetry_service)):
    result = await svc.speed_trace(body.year, body.race, body.session, body.driver, body.lap)
    if "error" in result:
        raise AppError("TELEMETRY_ERROR", result["error"], status_code=404)
    return result


@router.post("/driver-comparison")
async def driver_comparison(body: DriverComparisonRequest, svc=Depends(get_telemetry_service)):
    result = await svc.driver_comparison(body.year, body.race, body.session, body.driver1, body.driver2)
    return result


@router.post("/track-map")
async def track_map(body: TrackMapRequest, svc=Depends(get_telemetry_service)):
    result = await svc.track_map(body.year, body.race, body.session, body.driver, body.lap)
    if "error" in result:
        raise AppError("TELEMETRY_ERROR", result["error"], status_code=404)
    return result


@router.post("/weather-context")
async def weather_context(body: WeatherContextRequest, svc=Depends(get_telemetry_service)):
    result = await svc.weather_context(body.year, body.race, body.session)
    return result


@router.get("/sessions/{year}")
async def available_sessions(year: int, svc=Depends(get_telemetry_service)):
    return {"year": year, "sessions": await svc.available_sessions(year)}
```

**Step 4: Add telemetry provider to deps.py**

Add to `backend/app/deps.py`:

```python
from .services.telemetry import TelemetryService
from .config import settings

def get_telemetry_service(request: Request) -> TelemetryService:
    return TelemetryService(cache_dir=settings.resolved_fastf1_dir())
```

**Step 5: Commit**

```bash
git add backend/app/services/telemetry.py backend/app/models/telemetry.py backend/app/routers/telemetry.py backend/app/deps.py
git commit -m "feat: telemetry service + router — FastF1 via thread pool executor"
```

---

## Task 10: Strategy Service + Router

Port `services/strategy_simulation_service.py`. Keep the Monte Carlo tire simulation — it's solid. Wire Gemini as optional.

**Files:**
- Create: `backend/app/services/strategy.py`
- Create: `backend/app/models/strategy.py`
- Create: `backend/app/routers/strategy.py`

**Step 1: Write models/strategy.py**

```python
# backend/app/models/strategy.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class StrategyRequest(BaseModel):
    driver: str
    track: str
    laps: int = Field(default=57, ge=10, le=78)
    starting_tire: str = "MEDIUM"  # SOFT | MEDIUM | HARD
    weather: str = "dry"
    year: Optional[int] = None

class StrategyCompareRequest(BaseModel):
    driver: str
    track: str
    laps: int = 57
    strategies: List[List[str]]   # e.g. [["SOFT","HARD"], ["MEDIUM","MEDIUM"]]
    weather: str = "dry"

class StrategyOptimizeRequest(BaseModel):
    driver: str
    track: str
    laps: int = 57
    weather: str = "dry"
    use_ai: bool = False

class StintResult(BaseModel):
    stint: int
    tire: str
    start_lap: int
    end_lap: int
    laps: int
    avg_lap_time: float
    degradation: str

class StrategyResult(BaseModel):
    strategy_id: str
    driver: str
    track: str
    total_time: float
    pit_stops: int
    stints: List[StintResult]
    final_position_estimate: int
    summary: str
```

**Step 2: Write services/strategy.py**

Port the core logic from `services/strategy_simulation_service.py`. Key tyre degradation model and pit timing:

```python
# backend/app/services/strategy.py
"""
F1 Strategy simulation service.
Ported from strategy_simulation_service.py — same degradation model,
cleaner async interface, optional Gemini AI optimize.
"""
import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="strategy_")

TIRE_COMPOUNDS = {
    "SOFT":   {"base_delta": 0.0,  "deg_rate": 0.12, "peak_laps": 15},
    "MEDIUM": {"base_delta": 0.5,  "deg_rate": 0.07, "peak_laps": 25},
    "HARD":   {"base_delta": 1.0,  "deg_rate": 0.04, "peak_laps": 35},
    "INTER":  {"base_delta": -2.0, "deg_rate": 0.06, "peak_laps": 25},
    "WET":    {"base_delta": -5.0, "deg_rate": 0.05, "peak_laps": 30},
}

BASE_LAP_TIME = 90.0  # seconds — track-specific override via track_chars
PIT_LOSS      = 22.0  # seconds per pit stop


def _tire_lap_time(compound: str, lap_in_stint: int) -> float:
    t = TIRE_COMPOUNDS.get(compound, TIRE_COMPOUNDS["MEDIUM"])
    deg = t["deg_rate"] * max(0, lap_in_stint - t["peak_laps"])
    return BASE_LAP_TIME + t["base_delta"] + deg


def _simulate_strategy(
    driver: str, track: str, laps: int,
    stint_compounds: List[str], weather: str,
) -> Dict:
    stints = []
    total_time = 0.0
    lap = 1
    for i, compound in enumerate(stint_compounds):
        is_last = i == len(stint_compounds) - 1
        stint_laps = laps // len(stint_compounds)
        if is_last:
            stint_laps = laps - (len(stint_compounds) - 1) * (laps // len(stint_compounds))

        stint_time = 0.0
        for lap_in_stint in range(1, stint_laps + 1):
            stint_time += _tire_lap_time(compound, lap_in_stint)

        if not is_last:
            stint_time += PIT_LOSS  # pit stop loss at end of stint

        avg = stint_time / stint_laps
        deg_level = "Low" if avg < BASE_LAP_TIME + 1 else "Medium" if avg < BASE_LAP_TIME + 2 else "High"

        stints.append({
            "stint": i + 1,
            "tire": compound,
            "start_lap": lap,
            "end_lap": lap + stint_laps - 1,
            "laps": stint_laps,
            "avg_lap_time": round(avg, 3),
            "degradation": deg_level,
        })
        total_time += stint_time
        lap += stint_laps

    pit_stops = len(stint_compounds) - 1
    pos_estimate = max(1, min(20, 8 - pit_stops + int(total_time % 3)))

    return {
        "strategy_id": str(uuid.uuid4())[:8],
        "driver": driver,
        "track": track,
        "total_time": round(total_time, 2),
        "pit_stops": pit_stops,
        "stints": stints,
        "final_position_estimate": pos_estimate,
        "summary": f"{pit_stops}-stop {'-'.join(stint_compounds)} strategy",
    }


class StrategyService:
    async def simulate(
        self, driver: str, track: str, laps: int,
        starting_tire: str, weather: str,
    ) -> Dict:
        compounds = _choose_compounds(starting_tire, laps, weather)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, _simulate_strategy, driver, track, laps, compounds, weather
        )

    async def compare(
        self, driver: str, track: str, laps: int,
        strategies: List[List[str]], weather: str,
    ) -> List[Dict]:
        loop = asyncio.get_event_loop()
        results = []
        for s in strategies:
            r = await loop.run_in_executor(
                _executor, _simulate_strategy, driver, track, laps, s, weather
            )
            results.append(r)
        results.sort(key=lambda x: x["total_time"])
        return results

    async def optimize(
        self, driver: str, track: str, laps: int,
        weather: str, use_ai: bool = False,
    ) -> Dict:
        # Simulate candidate strategies
        candidates = [
            ["SOFT", "HARD"],
            ["MEDIUM", "MEDIUM"],
            ["SOFT", "MEDIUM", "HARD"],
            ["MEDIUM", "HARD"],
            ["SOFT", "SOFT", "HARD"],
        ]
        loop = asyncio.get_event_loop()
        results = []
        for s in candidates:
            r = await loop.run_in_executor(
                _executor, _simulate_strategy, driver, track, laps, s, weather
            )
            results.append(r)
        results.sort(key=lambda x: x["total_time"])
        best = results[0]

        if use_ai:
            ai_insight = await _gemini_insight(best, results[:3], driver, track, weather)
            best["ai_insight"] = ai_insight

        return {"optimal": best, "alternatives": results[1:3]}

    def get_tire_compounds(self, track: str) -> Dict:
        return {
            compound: {
                "base_delta_s": data["base_delta"],
                "degradation_rate": data["deg_rate"],
                "peak_laps": data["peak_laps"],
            }
            for compound, data in TIRE_COMPOUNDS.items()
        }

    def get_available_tracks(self) -> List[str]:
        import json, os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "track_characteristics.json")
        try:
            with open(path) as f:
                return list(json.load(f).keys())
        except Exception:
            return []


def _choose_compounds(starting: str, laps: int, weather: str) -> List[str]:
    if weather.lower() in ("wet", "heavy rain"):
        return ["WET", "WET"] if laps > 40 else ["WET"]
    if laps <= 30:
        return [starting, "HARD"]
    return [starting, "MEDIUM", "HARD"] if laps > 55 else [starting, "HARD"]


async def _gemini_insight(best: Dict, top3: List[Dict], driver: str, track: str, weather: str) -> str:
    try:
        import os
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            return "AI insights unavailable (no API key configured)"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"F1 strategy for {driver} at {track} ({weather} conditions).\n"
            f"Best strategy: {best['summary']} ({best['total_time']}s total).\n"
            f"Alternatives: {[s['summary'] for s in top3[1:]]}.\n"
            "Give a 2-sentence strategic recommendation."
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        logger.warning(f"Gemini insight failed: {e}")
        return "AI insight unavailable"
```

**Step 3: Write routers/strategy.py**

```python
# backend/app/routers/strategy.py
from fastapi import APIRouter, Depends
from ..models.strategy import (
    StrategyRequest, StrategyCompareRequest, StrategyOptimizeRequest,
)
from ..deps import get_strategy_service

router = APIRouter(tags=["strategy"])


@router.post("/simulate")
async def simulate(body: StrategyRequest, svc=Depends(get_strategy_service)):
    return await svc.simulate(body.driver, body.track, body.laps, body.starting_tire, body.weather)


@router.post("/compare")
async def compare(body: StrategyCompareRequest, svc=Depends(get_strategy_service)):
    return await svc.compare(body.driver, body.track, body.laps, body.strategies, body.weather)


@router.post("/optimize")
async def optimize(body: StrategyOptimizeRequest, svc=Depends(get_strategy_service)):
    return await svc.optimize(body.driver, body.track, body.laps, body.weather, body.use_ai)


@router.get("/tire-compounds/{track}")
async def tire_compounds(track: str, svc=Depends(get_strategy_service)):
    return svc.get_tire_compounds(track)


@router.get("/tracks")
async def available_tracks(svc=Depends(get_strategy_service)):
    return {"tracks": svc.get_available_tracks()}
```

**Step 4: Add to deps.py**

```python
from .services.strategy import StrategyService

def get_strategy_service(request: Request) -> StrategyService:
    return StrategyService()
```

**Step 5: Commit**

```bash
git add backend/app/services/strategy.py backend/app/models/strategy.py backend/app/routers/strategy.py backend/app/deps.py
git commit -m "feat: strategy service + router — tire sim, compare, optimize with optional Gemini"
```

---

## Task 11: Weather Service + Router

Port `services/live_weather_service.py` — replace `requests` with `aiohttp`, use the app's shared session.

**Files:**
- Create: `backend/app/services/weather.py`
- Create: `backend/app/routers/weather.py`

**Step 1: Write services/weather.py**

```python
# backend/app/services/weather.py
"""
Live weather service for F1 circuits.
Ports live_weather_service.py to fully async aiohttp.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Circuit coordinates — ported from live_weather_service.py
CIRCUITS: Dict[str, Dict] = {
    "Bahrain Grand Prix":        {"lat": 26.0325, "lon": 50.5106, "location": "Sakhir",         "country": "Bahrain"},
    "Saudi Arabian Grand Prix":  {"lat": 21.6322, "lon": 39.1044, "location": "Jeddah",          "country": "Saudi Arabia"},
    "Australian Grand Prix":     {"lat": -37.8497,"lon": 144.968,  "location": "Melbourne",       "country": "Australia"},
    "Japanese Grand Prix":       {"lat": 34.8431, "lon": 136.541,  "location": "Suzuka",          "country": "Japan"},
    "Chinese Grand Prix":        {"lat": 31.3389, "lon": 121.220,  "location": "Shanghai",        "country": "China"},
    "Miami Grand Prix":          {"lat": 25.9581, "lon": -80.2389, "location": "Miami",           "country": "USA"},
    "Emilia Romagna Grand Prix": {"lat": 44.3439, "lon": 11.7167,  "location": "Imola",           "country": "Italy"},
    "Monaco Grand Prix":         {"lat": 43.7347, "lon":  7.4205,  "location": "Monte Carlo",     "country": "Monaco"},
    "Canadian Grand Prix":       {"lat": 45.5048, "lon": -73.5225, "location": "Montreal",        "country": "Canada"},
    "Spanish Grand Prix":        {"lat": 41.5700, "lon":  2.2617,  "location": "Barcelona",       "country": "Spain"},
    "Austrian Grand Prix":       {"lat": 47.2197, "lon": 14.7647,  "location": "Spielberg",       "country": "Austria"},
    "British Grand Prix":        {"lat": 52.0786, "lon": -1.0169,  "location": "Silverstone",     "country": "UK"},
    "Hungarian Grand Prix":      {"lat": 47.5830, "lon": 19.2526,  "location": "Budapest",        "country": "Hungary"},
    "Belgian Grand Prix":        {"lat": 50.4372, "lon":  5.9714,  "location": "Spa",             "country": "Belgium"},
    "Dutch Grand Prix":          {"lat": 52.3881, "lon":  4.5400,  "location": "Zandvoort",       "country": "Netherlands"},
    "Italian Grand Prix":        {"lat": 45.6156, "lon":  9.2811,  "location": "Monza",           "country": "Italy"},
    "Azerbaijan Grand Prix":     {"lat": 40.3725, "lon": 49.8533,  "location": "Baku",            "country": "Azerbaijan"},
    "Singapore Grand Prix":      {"lat":  1.2914, "lon": 103.864,  "location": "Singapore",       "country": "Singapore"},
    "United States Grand Prix":  {"lat": 30.1328, "lon": -97.6411, "location": "Austin",          "country": "USA"},
    "Mexico City Grand Prix":    {"lat": 19.4042, "lon": -99.0907, "location": "Mexico City",     "country": "Mexico"},
    "São Paulo Grand Prix":      {"lat": -23.7036,"lon": -46.6997, "location": "São Paulo",       "country": "Brazil"},
    "Las Vegas Grand Prix":      {"lat": 36.1716, "lon": -115.140, "location": "Las Vegas",       "country": "USA"},
    "Qatar Grand Prix":          {"lat": 25.4900, "lon": 51.4542,  "location": "Lusail",          "country": "Qatar"},
    "Abu Dhabi Grand Prix":      {"lat": 24.4672, "lon": 54.6031,  "location": "Yas Marina",      "country": "UAE"},
}

_weather_cache: Dict[str, Dict] = {}  # {circuit: {data, expires}}
CACHE_SECS = 600


class WeatherService:
    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        self._key = api_key
        self._session = session
        self._base = "https://api.openweathermap.org/data/2.5"

    def _cached(self, circuit: str) -> Optional[Dict]:
        entry = _weather_cache.get(circuit)
        if entry and time.time() < entry["expires"]:
            return entry["data"]
        return None

    def _store(self, circuit: str, data: Dict):
        _weather_cache[circuit] = {"data": data, "expires": time.time() + CACHE_SECS}

    async def _owm_get(self, lat: float, lon: float) -> Optional[Dict]:
        if not self._key or not self._session:
            return None
        url = f"{self._base}/weather"
        params = {"lat": lat, "lon": lon, "appid": self._key, "units": "metric"}
        try:
            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning(f"OWM returned {resp.status}")
                return None
        except Exception as e:
            logger.error(f"OWM error: {e}")
            return None

    async def get_circuit_weather(self, circuit: str) -> Dict:
        cached = self._cached(circuit)
        if cached:
            return cached

        meta = CIRCUITS.get(circuit)
        if not meta:
            return _fallback_weather(circuit)

        raw = await self._owm_get(meta["lat"], meta["lon"])
        if not raw:
            return _fallback_weather(circuit, meta)

        data = _parse_owm(circuit, meta, raw)
        self._store(circuit, data)
        return data

    async def get_race_weekend_weather(self, circuit: str) -> Dict:
        current = await self.get_circuit_weather(circuit)
        return {
            "circuit": circuit,
            "current": current,
            "sessions_forecast": {
                "practice_1": _forecast_shift(current, -2),
                "practice_2": _forecast_shift(current, -1),
                "qualifying": _forecast_shift(current, 0),
                "race":       _forecast_shift(current, 1),
            },
        }

    def get_all_circuits(self) -> List[str]:
        return sorted(CIRCUITS.keys())


def _parse_owm(circuit: str, meta: Dict, raw: Dict) -> Dict:
    main = raw.get("main", {})
    wind = raw.get("wind", {})
    weather_list = raw.get("weather", [{}])
    desc = weather_list[0].get("description", "clear")
    rain_1h = raw.get("rain", {}).get("1h", 0.0)

    condition = "clear"
    if rain_1h > 5:
        condition = "heavy_rain"
    elif rain_1h > 0.5:
        condition = "light_rain"
    elif "cloud" in desc:
        condition = "overcast"

    track_temp = main.get("temp", 25) * 1.4  # rough estimation

    return {
        "circuit": circuit,
        "location": meta["location"],
        "country": meta["country"],
        "temperature_c": main.get("temp"),
        "feels_like_c": main.get("feels_like"),
        "humidity_pct": main.get("humidity"),
        "pressure_hpa": main.get("pressure"),
        "wind_speed_ms": wind.get("speed"),
        "wind_direction_deg": wind.get("deg"),
        "condition": condition,
        "description": desc,
        "precipitation_1h_mm": rain_1h,
        "track_temp_estimate_c": round(track_temp, 1),
        "grip_level": "Excellent" if condition == "clear" else "Good" if condition == "overcast" else "Poor",
    }


def _fallback_weather(circuit: str, meta: Dict = None) -> Dict:
    return {
        "circuit": circuit,
        "location": (meta or {}).get("location", "Unknown"),
        "condition": "unknown",
        "description": "Live weather unavailable — no API key or circuit not found",
        "temperature_c": None,
        "humidity_pct": None,
    }


def _forecast_shift(current: Dict, hour_offset: int) -> Dict:
    """Very simple forecast — shift temp slightly, keep condition."""
    result = dict(current)
    t = current.get("temperature_c")
    if t is not None:
        result["temperature_c"] = round(t + hour_offset * 0.5, 1)
    return result
```

**Step 2: Write routers/weather.py**

```python
# backend/app/routers/weather.py
from fastapi import APIRouter, Depends, Request
from ..deps import get_weather_service
from ..models.common import AppError

router = APIRouter(tags=["weather"])


@router.get("/circuits")
async def circuits(svc=Depends(get_weather_service)):
    return {"circuits": svc.get_all_circuits()}


@router.get("/current/{circuit:path}")
async def current_weather(circuit: str, svc=Depends(get_weather_service)):
    data = await svc.get_circuit_weather(circuit)
    return data


@router.get("/race-weekend/{circuit:path}")
async def race_weekend_weather(circuit: str, svc=Depends(get_weather_service)):
    return await svc.get_race_weekend_weather(circuit)
```

**Step 3: Add to deps.py**

```python
from .services.weather import WeatherService

def get_weather_service(request: Request) -> WeatherService:
    return WeatherService(
        api_key=settings.openweather_api_key,
        session=request.app.state.jolpica._session,  # reuse shared aiohttp session
    )
```

**Step 4: Commit**

```bash
git add backend/app/services/weather.py backend/app/routers/weather.py backend/app/deps.py
git commit -m "feat: weather service + router — fully async aiohttp, circuit coordinates"
```

---

## Task 12: Wire Up, Requirements, Entrypoint, Cleanup

**Files:**
- Create: `backend/app/routers/__init__.py`
- Modify: `backend/main.py`
- Modify: `backend/requirements.txt`
- Delete: `backend/services/` (old)
- Delete: `backend/api/` (old)

**Step 1: Create routers/__init__.py**

```python
# backend/app/routers/__init__.py
# empty
```

**Step 2: Update backend/main.py entry point**

```python
# backend/main.py
"""Thin entry point. Run with: uvicorn main:app --reload"""
from app.main import app

__all__ = ["app"]
```

**Step 3: Update requirements.txt**

Replace with slimmed down version — remove tensorflow, torch, optuna, xgboost, scikit-learn (no ML models):

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
aiohttp>=3.9.0
aiosqlite>=0.20.0
fastf1>=3.3.7
numpy>=1.26.0
pandas>=2.1.4
python-dotenv>=1.0.0
google-generativeai>=0.8.0
```

**Step 4: Smoke test — start the server**

```bash
cd backend && uvicorn main:app --reload --port 8000
```

Expected: Server starts in < 2s, logs show "F1 backend ready", no import errors.

**Step 5: Test key endpoints**

```bash
# Health check
curl http://localhost:8000/health

# Meta
curl http://localhost:8000/api/meta/drivers/2026

# Results
curl http://localhost:8000/api/results/standings?year=2026

# Prediction
curl -X POST http://localhost:8000/api/predict/race \
  -H "Content-Type: application/json" \
  -d '{"track": "Monaco Grand Prix", "weather": "dry"}'
```

**Step 6: Verify all routers load without 500 errors**

```bash
curl http://localhost:8000/openapi.json | python -c "import sys,json; d=json.load(sys.stdin); print(list(d['paths'].keys()))"
```

Expected: 20+ paths listed.

**Step 7: Delete old backend code**

```bash
rm -rf backend/services/ backend/api/
rm backend/enhanced_model_training.log 2>/dev/null || true
```

**Step 8: Final commit**

```bash
cd backend && git add -A
git commit -m "feat: complete backend rewrite — async DI architecture, ratings engine, no stale ML"
```

---

## Quick Reference: What Goes Where

| Old file | New location |
|---|---|
| `services/cache_manager.py` | `app/services/cache.py` + `app/services/jolpica.py` |
| `services/race_prediction_service.py` | `app/core/f1_ratings.py` + `app/core/monte_carlo.py` + `app/services/prediction.py` |
| `services/enhanced_prediction_service.py` | Replaced by `app/services/prediction.py` |
| `services/enhanced_ensemble_service.py` | Removed (stale ML) |
| `services/telemetry_analyzer_service.py` | `app/services/telemetry.py` |
| `services/strategy_simulation_service.py` | `app/services/strategy.py` |
| `services/live_weather_service.py` | `app/services/weather.py` |
| `services/f1_results_service.py` | `app/services/results.py` |
| `services/gemini_optimizer_service.py` | Inlined into `app/services/strategy.py` |
| `api/fastf1_routes.py` | `app/routers/results.py` + `app/routers/meta.py` |
| `api/metadata_routes.py` | `app/routers/meta.py` |
| `main.py` (1253 lines) | `app/main.py` (~80 lines) + `main.py` (3 lines) |

## Dependencies Removed

| Package | Why removed |
|---|---|
| `tensorflow` | ML models replaced by ratings engine |
| `torch` | Same |
| `scikit-learn` | Same |
| `xgboost` | Same |
| `optuna` | Hyperparameter tuning no longer needed |
| `requests` | Replaced by `aiohttp` throughout |
