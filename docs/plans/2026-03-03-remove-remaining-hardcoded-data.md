# Remove Remaining Hardcoded Data + SQLite Persistent Cache

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** (1) Eliminate all remaining hardcoded year-specific F1 data so the app adapts to any season automatically. (2) Add SQLite as a persistent cache layer so server restarts are instant — no re-fetching historical data from Jolpica API. (3) Enable FastF1 disk cache for telemetry.

**Architecture:** Two-tier cache: `Request → In-Memory Dict (instant) → SQLite (survives restarts) → Jolpica API (only for genuinely new data)`. Move all season-specific fallback data (driver/team ratings, rosters) into JSON config files under `backend/config/`. Replace hardcoded driver lookups with `cache_manager` calls. Fix year literals to use `datetime.now().year`. Enable FastF1's built-in disk cache for telemetry sessions.

**Tech Stack:** Python (FastAPI backend), SQLite3 (stdlib — no new dependencies), cache_manager singleton (already built), FastF1 disk cache, JSON config files, React/TypeScript frontend.

---

### Task 1: Extract driver roster from race_prediction_service.py to config

**Files:**
- Create: `backend/config/fallback_driver_roster.json`
- Modify: `backend/services/race_prediction_service.py:28-69`

**Step 1: Create the JSON config file**

```json
{
  "_comment": "Fallback driver roster. Used by prediction services when cache_manager has no data. Update each season.",
  "drivers": {
    "VER": {"name": "Max Verstappen", "team": "Red Bull Racing Honda RBPT", "number": 1},
    "TSU": {"name": "Yuki Tsunoda", "team": "Red Bull Racing Honda RBPT", "number": 22},
    "HAM": {"name": "Lewis Hamilton", "team": "Scuderia Ferrari", "number": 44},
    "LEC": {"name": "Charles Leclerc", "team": "Scuderia Ferrari", "number": 16},
    "RUS": {"name": "George Russell", "team": "Mercedes", "number": 63},
    "ANT": {"name": "Kimi Antonelli", "team": "Mercedes", "number": 12},
    "NOR": {"name": "Lando Norris", "team": "McLaren Mercedes", "number": 4},
    "PIA": {"name": "Oscar Piastri", "team": "McLaren Mercedes", "number": 81},
    "ALO": {"name": "Fernando Alonso", "team": "Aston Martin Aramco Mercedes", "number": 14},
    "STR": {"name": "Lance Stroll", "team": "Aston Martin Aramco Mercedes", "number": 18},
    "GAS": {"name": "Pierre Gasly", "team": "BWT Alpine F1 Team", "number": 10},
    "COL": {"name": "Franco Colapinto", "team": "BWT Alpine F1 Team", "number": 43},
    "LAW": {"name": "Liam Lawson", "team": "Racing Bulls F1 Team", "number": 30},
    "HAD": {"name": "Isack Hadjar", "team": "Racing Bulls F1 Team", "number": 6},
    "SAI": {"name": "Carlos Sainz", "team": "Williams Mercedes", "number": 55},
    "ALB": {"name": "Alexander Albon", "team": "Williams Mercedes", "number": 23},
    "OCO": {"name": "Esteban Ocon", "team": "MoneyGram Haas F1 Team", "number": 31},
    "BEA": {"name": "Oliver Bearman", "team": "MoneyGram Haas F1 Team", "number": 38},
    "HUL": {"name": "Nico Hulkenberg", "team": "Kick Sauber F1 Team", "number": 27},
    "BOR": {"name": "Gabriel Bortoleto", "team": "Kick Sauber F1 Team", "number": 5}
  }
}
```

**Step 2: Update race_prediction_service.py to load from cache_manager with JSON fallback**

Replace lines 28-69 in `race_prediction_service.py`:

```python
# At top of file, add:
import json

# In __init__, replace self.drivers_2025 = {...} with:
        self._fallback_roster = self._load_fallback_roster()

    def _load_fallback_roster(self) -> Dict:
        """Load fallback driver roster from JSON config."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fallback_driver_roster.json')
        try:
            with open(config_path) as f:
                return json.load(f).get("drivers", {})
        except Exception:
            logger.warning("Could not load fallback_driver_roster.json")
            return {}

    def _get_driver_roster(self, year: int = None) -> Dict:
        """Get driver roster: cache_manager first, fallback JSON second."""
        from services.cache_manager import cache_manager
        if year is None:
            from datetime import datetime, timezone
            year = datetime.now(timezone.utc).year
        drivers = cache_manager.get_drivers(year)
        if drivers:
            return {
                d["code"]: {"name": d["name"], "team": cache_manager.get_driver_team(d["code"], year), "number": int(d.get("number", 0)) if d.get("number", "").isdigit() else 0}
                for d in drivers if d.get("code")
            }
        return self._fallback_roster
```

Then find-and-replace every occurrence of `self.drivers_2025` with `self._get_driver_roster()` in the same file.

**Step 3: Verify import works**

Run: `cd backend && python3 -c "from services.race_prediction_service import RacePredictionService; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add backend/config/fallback_driver_roster.json backend/services/race_prediction_service.py
git commit -m "refactor: extract driver roster from race_prediction_service to JSON config with cache_manager lookup"
```

---

### Task 2: Extract team performance ratings to config

**Files:**
- Create: `backend/config/fallback_team_ratings.json`
- Create: `backend/config/fallback_driver_ratings.json`
- Modify: `backend/services/race_prediction_service.py:605-698`

**Step 1: Create team ratings JSON**

```json
{
  "_comment": "Fallback team car performance ratings. Used when ML models can't compute from data. Update each season.",
  "teams": {
    "McLaren Mercedes": {"dry_pace": 0.94, "wet_pace": 0.91, "strategy": 0.88, "reliability": 0.87},
    "Red Bull Racing Honda RBPT": {"dry_pace": 0.89, "wet_pace": 0.92, "strategy": 0.90, "reliability": 0.85},
    "Mercedes": {"dry_pace": 0.85, "wet_pace": 0.88, "strategy": 0.83, "reliability": 0.86},
    "Scuderia Ferrari": {"dry_pace": 0.82, "wet_pace": 0.80, "strategy": 0.75, "reliability": 0.78},
    "Williams Mercedes": {"dry_pace": 0.78, "wet_pace": 0.76, "strategy": 0.74, "reliability": 0.80},
    "MoneyGram Haas F1 Team": {"dry_pace": 0.76, "wet_pace": 0.74, "strategy": 0.72, "reliability": 0.77},
    "Kick Sauber F1 Team": {"dry_pace": 0.75, "wet_pace": 0.73, "strategy": 0.70, "reliability": 0.75},
    "BWT Alpine F1 Team": {"dry_pace": 0.73, "wet_pace": 0.72, "strategy": 0.68, "reliability": 0.74},
    "Racing Bulls F1 Team": {"dry_pace": 0.72, "wet_pace": 0.71, "strategy": 0.67, "reliability": 0.73},
    "Aston Martin Aramco Mercedes": {"dry_pace": 0.68, "wet_pace": 0.66, "strategy": 0.65, "reliability": 0.70}
  },
  "default": {"dry_pace": 0.70, "wet_pace": 0.70, "strategy": 0.70, "reliability": 0.75}
}
```

**Step 2: Create driver ratings JSON**

```json
{
  "_comment": "Fallback driver skill ratings. Used when ML models can't compute from data. Update each season.",
  "drivers": {
    "Max Verstappen": {"overall_skill": 0.95, "wet_skill": 0.95, "race_craft": 0.93, "strategy_execution": 0.90},
    "Oscar Piastri": {"overall_skill": 0.94, "wet_skill": 0.88, "race_craft": 0.92, "strategy_execution": 0.90},
    "Lando Norris": {"overall_skill": 0.92, "wet_skill": 0.86, "race_craft": 0.89, "strategy_execution": 0.88},
    "Lewis Hamilton": {"overall_skill": 0.88, "wet_skill": 0.93, "race_craft": 0.90, "strategy_execution": 0.85},
    "George Russell": {"overall_skill": 0.86, "wet_skill": 0.84, "race_craft": 0.85, "strategy_execution": 0.87},
    "Charles Leclerc": {"overall_skill": 0.85, "wet_skill": 0.82, "race_craft": 0.84, "strategy_execution": 0.80},
    "Fernando Alonso": {"overall_skill": 0.84, "wet_skill": 0.88, "race_craft": 0.87, "strategy_execution": 0.85},
    "Carlos Sainz": {"overall_skill": 0.82, "wet_skill": 0.79, "race_craft": 0.83, "strategy_execution": 0.82},
    "Yuki Tsunoda": {"overall_skill": 0.79, "wet_skill": 0.76, "race_craft": 0.78, "strategy_execution": 0.75},
    "Alexander Albon": {"overall_skill": 0.78, "wet_skill": 0.75, "race_craft": 0.79, "strategy_execution": 0.80},
    "Nico Hulkenberg": {"overall_skill": 0.78, "wet_skill": 0.80, "race_craft": 0.77, "strategy_execution": 0.82},
    "Pierre Gasly": {"overall_skill": 0.77, "wet_skill": 0.79, "race_craft": 0.76, "strategy_execution": 0.78},
    "Esteban Ocon": {"overall_skill": 0.76, "wet_skill": 0.74, "race_craft": 0.75, "strategy_execution": 0.77},
    "Liam Lawson": {"overall_skill": 0.74, "wet_skill": 0.71, "race_craft": 0.73, "strategy_execution": 0.70},
    "Kimi Antonelli": {"overall_skill": 0.73, "wet_skill": 0.70, "race_craft": 0.71, "strategy_execution": 0.68},
    "Franco Colapinto": {"overall_skill": 0.72, "wet_skill": 0.69, "race_craft": 0.71, "strategy_execution": 0.68},
    "Isack Hadjar": {"overall_skill": 0.72, "wet_skill": 0.69, "race_craft": 0.71, "strategy_execution": 0.68},
    "Oliver Bearman": {"overall_skill": 0.71, "wet_skill": 0.68, "race_craft": 0.70, "strategy_execution": 0.67},
    "Gabriel Bortoleto": {"overall_skill": 0.70, "wet_skill": 0.67, "race_craft": 0.69, "strategy_execution": 0.66},
    "Lance Stroll": {"overall_skill": 0.68, "wet_skill": 0.65, "race_craft": 0.66, "strategy_execution": 0.67}
  },
  "default": {"overall_skill": 0.70, "wet_skill": 0.68, "race_craft": 0.68, "strategy_execution": 0.68}
}
```

**Step 3: Replace `_set_fallback_car_ratings` and `_set_fallback_driver_ratings` in race_prediction_service.py**

Replace methods at lines 605-675 with:

```python
    def _set_fallback_car_ratings(self):
        """Load fallback car ratings from JSON config."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fallback_team_ratings.json')
        try:
            with open(config_path) as f:
                data = json.load(f)
                self.car_performance = data.get("teams", {})
        except Exception:
            self.car_performance = {}
        logger.warning("Using fallback car performance ratings from config")

    def _set_fallback_driver_ratings(self):
        """Load fallback driver ratings from JSON config."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fallback_driver_ratings.json')
        try:
            with open(config_path) as f:
                data = json.load(f)
                self.driver_performance = data.get("drivers", {})
        except Exception:
            self.driver_performance = {}
        logger.warning("Using fallback driver performance ratings from config")
```

Also replace `_get_team_fallback_rating` (lines 684-699) and `_get_driver_fallback_rating` (lines 701+) to read from the same JSON:

```python
    def _get_team_fallback_rating(self, team: str) -> Dict:
        """Get fallback rating for a specific team from config."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fallback_team_ratings.json')
        try:
            with open(config_path) as f:
                data = json.load(f)
                return data["teams"].get(team, data.get("default", {}))
        except Exception:
            return {'dry_pace': 0.70, 'wet_pace': 0.70, 'strategy': 0.70, 'reliability': 0.75}

    def _get_driver_fallback_rating(self, driver_name: str) -> Dict:
        """Get fallback rating for a specific driver from config."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fallback_driver_ratings.json')
        try:
            with open(config_path) as f:
                data = json.load(f)
                return data["drivers"].get(driver_name, data.get("default", {}))
        except Exception:
            return {'overall_skill': 0.70, 'wet_skill': 0.68, 'race_craft': 0.68, 'strategy_execution': 0.68}
```

**Step 4: Verify import**

Run: `cd backend && python3 -c "from services.race_prediction_service import RacePredictionService; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add backend/config/fallback_team_ratings.json backend/config/fallback_driver_ratings.json backend/services/race_prediction_service.py
git commit -m "refactor: extract team and driver performance ratings to JSON config files"
```

---

### Task 3: Fix enhanced_prediction_service.py hardcoded data

**Files:**
- Modify: `backend/services/enhanced_prediction_service.py:40-67, 221-239`

**Step 1: Replace hardcoded driver name mapping (lines ~40-54) with cache_manager lookup**

Replace the hardcoded `self.current_drivers` dict with:

```python
    def _get_current_drivers(self) -> Dict[str, str]:
        """Get driver code->name mapping from cache, fallback to config."""
        from services.cache_manager import cache_manager
        from datetime import datetime, timezone
        year = datetime.now(timezone.utc).year
        code_map = cache_manager.get_driver_code_map(year)
        if code_map:
            return code_map
        # Fallback to roster config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fallback_driver_roster.json')
        try:
            with open(config_path) as f:
                data = json.load(f).get("drivers", {})
                return {code: info["name"] for code, info in data.items()}
        except Exception:
            return {}
```

**Step 2: Replace hardcoded `self.current_teams` (lines 56-67) with cache_manager lookup**

```python
    def _get_current_teams(self) -> Dict[str, str]:
        """Get team short->full name mapping from cache, fallback to config."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'team_name_mapping.json')
        try:
            with open(config_path) as f:
                return json.load(f).get("teams", {})
        except Exception:
            return {}
```

Create `backend/config/team_name_mapping.json`:

```json
{
  "_comment": "Maps short team names to full official names. Update each season.",
  "teams": {
    "Red Bull": "Red Bull Racing Honda RBPT",
    "Ferrari": "Scuderia Ferrari",
    "Mercedes": "Mercedes",
    "McLaren": "McLaren Mercedes",
    "Aston Martin": "Aston Martin Aramco Mercedes",
    "Alpine": "BWT Alpine F1 Team",
    "AlphaTauri": "Visa Cash App RB F1 Team",
    "Racing Bulls": "Racing Bulls F1 Team",
    "Williams": "Williams Mercedes",
    "Haas": "MoneyGram Haas F1 Team",
    "Kick Sauber": "Kick Sauber F1 Team"
  }
}
```

**Step 3: Replace fallback methods (lines 221-239) to load from JSON configs**

Same pattern as Task 2 — read from `fallback_team_ratings.json` and `fallback_driver_ratings.json`.

**Step 4: Verify import**

Run: `cd backend && python3 -c "from services.enhanced_prediction_service import EnhancedPredictionService; print('OK')"`

**Step 5: Commit**

```bash
git add backend/config/team_name_mapping.json backend/services/enhanced_prediction_service.py
git commit -m "refactor: replace hardcoded driver/team data in enhanced_prediction_service with config + cache"
```

---

### Task 4: Fix enhanced_ml_model.py hardcoded driver roster

**Files:**
- Modify: `backend/enhanced_ml_model.py:165-187`

**Step 1: Replace hardcoded `drivers_2025` dict with config loader**

Replace lines 165-187 with:

```python
        # Load driver roster from config (keyed by number for session data matching)
        drivers_by_number = self._load_drivers_by_number()
```

Add helper method:

```python
    def _load_drivers_by_number(self) -> Dict:
        """Load driver roster keyed by car number from config."""
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'fallback_driver_roster.json')
        try:
            with open(config_path) as f:
                data = json.load(f).get("drivers", {})
                return {
                    str(info["number"]): {"code": code, "name": info["name"], "team": info["team"]}
                    for code, info in data.items()
                }
        except Exception:
            return {}
```

Then replace all `drivers_2025` references in the method with `drivers_by_number`.

**Step 2: Verify import**

Run: `cd backend && python3 -c "from enhanced_ml_model import EnhancedF1MLModel; print('OK')"`

**Step 3: Commit**

```bash
git add backend/enhanced_ml_model.py
git commit -m "refactor: replace hardcoded driver roster in enhanced_ml_model with config loader"
```

---

### Task 5: Fix prediction_service.py hardcoded mappings

**Files:**
- Modify: `backend/services/prediction_service.py:25-96`

**Step 1: Replace `self.driver_mapping` (lines 25-46) with cache_manager + fallback**

```python
    def _get_driver_mapping(self) -> Dict[str, str]:
        """Get driver code->name map from cache, fallback to config."""
        from services.cache_manager import cache_manager
        from datetime import datetime, timezone
        year = datetime.now(timezone.utc).year
        code_map = cache_manager.get_driver_code_map(year)
        if code_map:
            return code_map
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fallback_driver_roster.json')
        try:
            with open(config_path) as f:
                data = json.load(f).get("drivers", {})
                return {code: info["name"] for code, info in data.items()}
        except Exception:
            return {}
```

**Step 2: Replace `self.team_mapping` (lines 48-59) with config loader**

Use the same `team_name_mapping.json` created in Task 3.

**Step 3: Replace `get_2025_driver_transfers` (lines 61-66)**

Delete this method entirely. It's only used for historical context and is year-specific. If needed, could be a config file, but it's dead code for any year except 2025.

**Step 4: Replace `_normalize_track_name` (lines 68-96)**

Replace with generic stripping:

```python
    def _normalize_track_name(self, track: str) -> str:
        """Normalize track names by stripping common suffixes."""
        return track.replace(' Grand Prix', '').strip()
```

The 24-entry mapping was doing exactly this — every value was just the name with " Grand Prix" removed.

**Step 5: Replace all `self.driver_mapping` usages with `self._get_driver_mapping()`**

**Step 6: Verify import**

Run: `cd backend && python3 -c "from services.prediction_service import PredictionService; print('OK')"`

**Step 7: Commit**

```bash
git add backend/services/prediction_service.py
git commit -m "refactor: replace hardcoded driver/team/track mappings in prediction_service with dynamic lookups"
```

---

### Task 6: Fix year literals and defaults

**Files:**
- Modify: `backend/services/telemetry_analyzer_service.py:1307`
- Modify: `backend/services/fastf1_service.py:30`
- Modify: `backend/services/f1_results_service.py:448, 471, 539`
- Modify: `backend/services/f1_results_service.py:97` (rename property)

**Step 1: Fix telemetry_analyzer_service.py line 1307**

Replace `year = 2024` with:

```python
            from datetime import datetime, timezone
            year = datetime.now(timezone.utc).year
```

**Step 2: Fix fastf1_service.py line 30**

Replace `def get_driver_weather_performance(self, year: int = 2025)` with:

```python
    def get_driver_weather_performance(self, year: int = None) -> List[Dict]:
        if year is None:
            from datetime import datetime, timezone
            year = datetime.now(timezone.utc).year
```

**Step 3: Fix f1_results_service.py round count fallbacks**

At lines 448 and 539, change `else 24` to `else 0`:

```python
total_rounds = len(schedule) if schedule else 0
```

At line 471, change the log message:

```python
logger.info(f"Updated championship standings - Round {current_round}/{total_rounds}")
```

**Step 4: Rename `f1_calendar_2025` property to `f1_calendar`**

In `f1_results_service.py`, rename the property at line 97 from `f1_calendar_2025` to `f1_calendar`, then find-and-replace all usages of `f1_calendar_2025` with `f1_calendar` in the same file.

**Step 5: Verify imports**

Run: `cd backend && python3 -c "from services.telemetry_analyzer_service import TelemetryAnalyzerService; from services.fastf1_service import FastF1Service; from services.f1_results_service import F1ResultsService; print('OK')"`

**Step 6: Commit**

```bash
git add backend/services/telemetry_analyzer_service.py backend/services/fastf1_service.py backend/services/f1_results_service.py
git commit -m "fix: replace hardcoded year literals and round counts with dynamic values"
```

---

### Task 7: Fix download_current_data.py hardcoded calendar

**Files:**
- Modify: `backend/download_current_data.py:140-165`

**Step 1: Replace hardcoded calendar with cache_manager or FastF1 event schedule**

Replace `self.race_calendar_2025` (lines 140-165) with:

```python
        # Race calendar loaded dynamically from FastF1
        self.race_calendar = self._load_race_calendar()

    def _load_race_calendar(self) -> List[str]:
        """Load race calendar from FastF1 event schedule."""
        try:
            import fastf1
            from datetime import datetime
            year = datetime.now().year
            schedule = fastf1.get_event_schedule(year)
            return [row['EventName'] for _, row in schedule.iterrows() if row['EventFormat'] != 'testing']
        except Exception:
            logger.warning("Could not load dynamic calendar, using config fallback")
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'fallback_driver_roster.json')
            # If needed, could create a separate calendar config
            return []
```

Then replace all `self.race_calendar_2025` references with `self.race_calendar`.

**Step 2: Verify import**

Run: `cd backend && python3 -c "from download_current_data import F1DataDownloader; print('OK')"`

**Step 3: Commit**

```bash
git add backend/download_current_data.py
git commit -m "refactor: replace hardcoded race calendar in download_current_data with dynamic FastF1 schedule"
```

---

### Task 8: Fix frontend placeholder text

**Files:**
- Modify: `src/components/PredictionForm.tsx:69`

**Step 1: Replace hardcoded "2025" in placeholder**

Change:
```tsx
placeholder="Select a 2025 Grand Prix"
```
To:
```tsx
placeholder="Select a Grand Prix"
```

**Step 2: Commit**

```bash
git add src/components/PredictionForm.tsx
git commit -m "fix: remove hardcoded year from PredictionForm placeholder"
```

---

### Task 9: Final verification

**Step 1: Search for any remaining hardcoded year references**

Run: `cd /Users/pratyush/F1-Insight-Hub && grep -rn "2025" --include="*.py" --include="*.tsx" --include="*.ts" backend/ src/ | grep -v __pycache__ | grep -v node_modules | grep -v "comment\|Comment\|_comment\|#.*2025\|//.*2025\|\.md"`

Review each result — anything that's a live code reference (not a comment) to "2025" needs fixing.

**Step 2: Verify backend starts**

Run: `cd backend && python3 -c "from main import app; print('FastAPI app created OK')"`

**Step 3: Final commit if any fixes needed from grep audit**

```bash
git add -A
git commit -m "refactor: final cleanup of remaining hardcoded year references"
```

---

## Part 2: SQLite Persistent Cache + FastF1 Disk Cache

---

### Task 10: Add SQLite persistence layer to CacheManager

**Files:**
- Modify: `backend/services/cache_manager.py`

This is the core change. The CacheManager currently uses only an in-memory dict. We add SQLite as a persistence layer so that on restart, historical data loads from disk instantly instead of making ~20+ API calls.

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS cache_entries (
    key TEXT PRIMARY KEY,
    data TEXT NOT NULL,        -- JSON-serialized
    fetched_at TEXT NOT NULL,  -- ISO8601 UTC timestamp
    ttl_seconds INTEGER NOT NULL DEFAULT 0
);
```

**Step 1: Add SQLite storage class inside cache_manager.py**

Add after the `CacheEntry` dataclass, before the `CacheManager` class:

```python
import sqlite3
import json as json_module

class CacheStore:
    """SQLite-backed persistent cache store."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                ttl_seconds INTEGER NOT NULL DEFAULT 0
            )
        """)
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()

    def get(self, key: str) -> Optional[CacheEntry]:
        if not self._conn:
            return None
        row = self._conn.execute(
            "SELECT data, fetched_at, ttl_seconds FROM cache_entries WHERE key = ?",
            (key,)
        ).fetchone()
        if not row:
            return None
        return CacheEntry(
            data=json_module.loads(row[0]),
            fetched_at=datetime.fromisoformat(row[1]),
            ttl_seconds=row[2],
        )

    def set(self, key: str, entry: CacheEntry):
        if not self._conn:
            return
        self._conn.execute(
            "INSERT OR REPLACE INTO cache_entries (key, data, fetched_at, ttl_seconds) VALUES (?, ?, ?, ?)",
            (key, json_module.dumps(entry.data), entry.fetched_at.isoformat(), entry.ttl_seconds)
        )
        self._conn.commit()

    def get_keys_for_year(self, year: int) -> List[str]:
        """Check if we have any cached data for a given year."""
        if not self._conn:
            return []
        rows = self._conn.execute(
            "SELECT key FROM cache_entries WHERE key LIKE ?",
            (f"%:{year}%",)
        ).fetchall()
        return [r[0] for r in rows]
```

Add `import os` at top if not already there.

**Step 2: Integrate CacheStore into CacheManager.__init__**

```python
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._store = CacheStore()
        self._refresh_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        self._current_year: int = datetime.now(timezone.utc).year
        self._loaded_years: set = set()
        self._loading_locks: Dict[int, asyncio.Lock] = {}
```

**Step 3: Update `initialize()` to hydrate from SQLite first**

In `initialize()`, after creating the aiohttp session and before `_full_load`:

```python
        self._store.connect()
        self._hydrate_from_store()
```

Add hydration method:

```python
    def _hydrate_from_store(self):
        """Load all non-expired entries from SQLite into memory on startup."""
        if not self._store._conn:
            return
        rows = self._store._conn.execute(
            "SELECT key, data, fetched_at, ttl_seconds FROM cache_entries"
        ).fetchall()
        loaded = 0
        for key, data_json, fetched_at_str, ttl in rows:
            entry = CacheEntry(
                data=json_module.loads(data_json),
                fetched_at=datetime.fromisoformat(fetched_at_str),
                ttl_seconds=ttl,
            )
            # Always load permanent entries; load volatile only if not expired
            if ttl == 0 or not entry.is_expired:
                self._cache[key] = entry
                loaded += 1
                # Track which years we have data for
                parts = key.split(":")
                if len(parts) >= 2 and parts[1].isdigit():
                    self._loaded_years.add(int(parts[1]))
        logger.info(f"Hydrated {loaded} cache entries from SQLite ({len(self._loaded_years)} years)")
```

**Step 4: Update `_set()` to write-through to SQLite**

```python
    def _set(self, key: str, data: Any, ttl: int):
        entry = CacheEntry(
            data=data,
            fetched_at=datetime.now(timezone.utc),
            ttl_seconds=ttl,
        )
        self._cache[key] = entry
        self._store.set(key, entry)
```

**Step 5: Update `shutdown()` to close SQLite**

Add `self._store.close()` before the session close.

**Step 6: Update `_full_load()` to skip already-cached permanent data**

In `_full_load`, the race result loop already checks `if not self._cache.get(...)` before fetching — this naturally skips results loaded from SQLite. No change needed there.

For metadata (schedule, drivers, etc.), only refetch if expired or missing:

```python
    async def _full_load(self, year: int):
        """Load everything for a year. Skips data already cached from SQLite."""
        logger.info(f"Starting cache load for {year}...")

        # Only fetch metadata if not already in memory (or expired)
        if not self._cache.get(f"schedule:{year}") or self._cache[f"schedule:{year}"].is_expired:
            await self._fetch_schedule(year)
        if not self._cache.get(f"drivers:{year}") or self._cache[f"drivers:{year}"].is_expired:
            await self._fetch_drivers(year)
        if not self._cache.get(f"constructors:{year}") or self._cache[f"constructors:{year}"].is_expired:
            await self._fetch_constructors(year)

        # Standings: always refresh (1hr TTL, likely expired between restarts)
        await self._fetch_driver_standings(year)
        await self._fetch_constructor_standings(year)

        # Race results: permanent, skip if already in SQLite
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

        logger.info(f"Cache load complete for {year}")
```

**Step 7: Verify import**

Run: `cd backend && python3 -c "from services.cache_manager import cache_manager; print('OK')"`

**Step 8: Commit**

```bash
git add backend/services/cache_manager.py
git commit -m "feat: add SQLite persistent cache layer to CacheManager for instant restarts"
```

---

### Task 11: Enable FastF1 disk cache

**Files:**
- Modify: `backend/main.py` (startup event)
- Modify: `backend/services/fastf1_service.py` (if cache not already enabled)
- Modify: `backend/services/telemetry_analyzer_service.py` (if cache not already enabled)

FastF1 has built-in disk caching via `fastf1.Cache.enable_cache(path)`. When enabled, session data is cached to disk — subsequent loads of the same session go from ~30s to ~2s.

**Step 1: Check current FastF1 cache configuration**

Search for `fastf1.Cache` or `enable_cache` in the codebase. If it's already called somewhere, just verify the path exists. If not, add it.

**Step 2: Add FastF1 cache initialization in main.py startup**

In the startup event, before `cache_manager.initialize()`:

```python
        # Enable FastF1 disk cache for telemetry session data
        import fastf1
        fastf1_cache_dir = os.path.join(os.path.dirname(__file__), 'data', 'fastf1_cache')
        os.makedirs(fastf1_cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(fastf1_cache_dir)
        logger.info(f"FastF1 disk cache enabled at {fastf1_cache_dir}")
```

**Step 3: Add `backend/data/` to .gitignore**

This directory will contain the SQLite DB and FastF1 cache files — don't commit them.

```
# Cache data
backend/data/
```

**Step 4: Verify FastF1 cache works**

Run: `cd backend && python3 -c "import fastf1; import os; p = os.path.join(os.path.dirname('.'), 'data', 'fastf1_cache'); os.makedirs(p, exist_ok=True); fastf1.Cache.enable_cache(p); print('FastF1 cache OK')"`

**Step 5: Commit**

```bash
git add backend/main.py .gitignore
git commit -m "feat: enable FastF1 disk cache for instant telemetry reloads"
```

---

### Task 12: End-to-end verification

**Step 1: First cold start (populates SQLite)**

Start the server: `cd backend && python3 -m uvicorn main:app --port 8000`

Watch logs for:
- `CacheManager initialized for 2026` (fetches from API, writes to SQLite)
- `FastF1 disk cache enabled`

**Step 2: Kill and restart (should be near-instant)**

Kill the server, restart. Watch logs for:
- `Hydrated N cache entries from SQLite (M years)` — this means it loaded from disk
- Startup should complete in <1s instead of waiting for API calls

**Step 3: Test endpoints respond instantly**

```bash
curl -s localhost:8000/api/metadata/drivers/2026 | python3 -m json.tool | head -5
curl -s localhost:8000/api/f1/standings/2025 | python3 -m json.tool | head -5
curl -s localhost:8000/api/f1/dashboard/2026 | python3 -m json.tool | head -5
```

**Step 4: Verify SQLite file exists**

```bash
ls -la backend/data/cache.db
sqlite3 backend/data/cache.db "SELECT key FROM cache_entries LIMIT 10;"
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete performance optimization — SQLite cache + FastF1 disk cache + dynamic data"
```
