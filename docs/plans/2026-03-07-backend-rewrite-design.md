# Backend Rewrite Design — 2026-03-07

## Goal

Full rewrite of the F1-Insight-Hub backend to be faster, smarter, and cleaner.
Replace the 1,253-line `main.py` monolith with a properly structured, fully async
FastAPI application using dependency injection, aiosqlite, and a live-data-backed
prediction engine instead of stale `.pkl` ML models.

---

## Architecture

### File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # App factory + lifespan (~50 lines)
│   ├── deps.py              # FastAPI Depends() providers
│   ├── config.py            # Settings via pydantic-settings
│   │
│   ├── routers/
│   │   ├── predict.py       # /api/predict/*
│   │   ├── telemetry.py     # /api/telemetry/*
│   │   ├── strategy.py      # /api/strategy/*
│   │   ├── weather.py       # /api/weather/*
│   │   ├── results.py       # /api/results/*
│   │   └── meta.py          # /api/meta/*
│   │
│   ├── services/
│   │   ├── cache.py         # Async SQLite cache (aiosqlite)
│   │   ├── jolpica.py       # Jolpica API client (aiohttp)
│   │   ├── prediction.py    # Ratings-based prediction engine
│   │   ├── telemetry.py     # FastF1 wrapper (run_in_executor)
│   │   ├── strategy.py      # Strategy simulation
│   │   ├── weather.py       # Live weather
│   │   └── results.py       # Race results + standings
│   │
│   ├── models/
│   │   ├── predict.py       # Pydantic v2 prediction schemas
│   │   ├── telemetry.py
│   │   ├── strategy.py
│   │   └── common.py        # Shared types + error response
│   │
│   └── core/
│       ├── f1_ratings.py    # Dynamic ratings computation
│       └── monte_carlo.py   # Race outcome simulation
│
├── config/                  # JSON fallback configs (unchanged)
├── data/                    # cache.db (unchanged)
├── requirements.txt
└── main.py                  # Entry point: uvicorn app.main:app
```

### Key Principles

- No global service singletons — all services injected via `Depends()`
- `aiosqlite` for non-blocking SQLite access
- FastF1 calls wrapped in `asyncio.run_in_executor` (sync-only library)
- `lifespan` context manager replaces deprecated `@app.on_event`
- Single shared `aiohttp.ClientSession` for all Jolpica API calls
- Config JSON loaded once at startup into in-memory dict

---

## Prediction Engine

Replaces stale `.pkl` ML models with a live-data-backed ratings engine.

### Data Sources (priority order)

1. Live Jolpica standings — actual championship points, normalized to form factor
2. JSON config ratings — `fallback_driver_ratings.json`, `fallback_team_ratings.json`
3. Track characteristics — `track_characteristics.json`

### Rating Formula (`core/f1_ratings.py`)

```
driver_score = base_skill × team_performance × track_affinity × form_factor × weather_modifier
```

- `base_skill` — from config JSON (0–1 scale)
- `team_performance` — from live constructor standings (normalized 0–1)
- `track_affinity` — per-driver historical track weight from track config
- `form_factor` — last 3 race results vs expected (from Jolpica)
- `weather_modifier` — wet/dry multiplier per driver profile

### Race Simulation (`core/monte_carlo.py`)

- 1,000 iterations per call (~20ms)
- Each iteration: apply Gaussian noise to all driver scores, sort, record positions
- Output: win%, podium%, points% per driver
- Strategy variation injected at lap 25 and lap 45 as score modifiers

---

## Async Patterns & Caching

### Async Rules

| Operation | Pattern |
|---|---|
| Jolpica API calls | Native `aiohttp` — fully async |
| SQLite reads/writes | `aiosqlite` — non-blocking |
| FastF1 telemetry | `asyncio.run_in_executor(thread_pool)` |
| Config JSON | Loaded at startup, in-memory dict |
| Monte Carlo | `run_in_executor` (CPU-bound) |

### Cache Layers

```
Request
  → L1: In-memory dict (TTL per type)
      → L2: SQLite via aiosqlite (persistent across restarts)
          → L3: Jolpica API (aiohttp)
              → write back to L1 + L2
```

### TTLs

| Data | TTL |
|---|---|
| Live standings/results | 5 min |
| Schedule/calendar | 24 hours |
| Track characteristics | Permanent |
| Weather | 10 min |
| Telemetry sessions | Permanent once cached |

### Cold Start Target

< 2 seconds — no blocking downloads, no CSV loading.

---

## Error Handling & API Contracts

### Unified Error Shape

```json
{ "error": "DRIVER_NOT_FOUND", "message": "Driver 'XYZ' not found for 2026", "detail": null }
```

Single `AppError` exception class + global handler in `main.py`.
Services raise `AppError`, routers never catch-and-re-raise.

### Pydantic v2 Response Models

All endpoints have explicit `response_model=`. No raw dicts returned. Example:

```python
class RacePrediction(BaseModel):
    driver: str
    team: str
    predicted_position: int
    win_probability: float
    podium_probability: float
    expected_points: float
    key_factors: list[str]
```

### Dependency Injection

```python
# deps.py
async def get_cache(request: Request) -> CacheService: ...
async def get_jolpica(request: Request) -> JolpicaClient: ...
async def get_prediction_engine(request: Request) -> PredictionEngine: ...

# router
@router.post("/predict/race", response_model=RaceGridPrediction)
async def predict_race(
    body: RacePredictRequest,
    cache: CacheService = Depends(get_cache),
    engine: PredictionEngine = Depends(get_prediction_engine),
): ...
```

---

## Consolidated API Surface

### Old vs New

| Domain | Old (endpoints) | New |
|---|---|---|
| Prediction | 2 in main.py | `POST /api/predict/{driver,race}` |
| Results | 6 in main.py | `GET /api/results/{standings,calendar,next-race,recent}` + `POST /api/results/session` |
| Telemetry | 5 in main.py | `POST /api/telemetry/{analyze,speed-trace,driver-comparison,track-map,weather-context}` |
| Strategy | 5 in main.py | `POST /api/strategy/{simulate,compare,optimize}` + `GET /api/strategy/{tire-compounds,tracks}` |
| Weather | 3 in main.py | `POST /api/weather/{current,race-weekend}` + `GET /api/weather/circuits` |
| Meta | 4 across 2 routers | `GET /api/meta/{drivers,tracks,schedule,constructors}/{year}` |
| Health | 1 in main.py | `GET /health` |

Total: 30+ scattered endpoints → 22 clean endpoints across 6 routers.

---

## What Is Removed

- `main.py` monolith (1,253 lines) — replaced by `app/main.py` (~50 lines)
- All `.pkl` ML models — replaced by ratings engine + Monte Carlo
- `@app.on_event` deprecated hooks
- Global singleton service instances
- Blocking SQLite in async handlers
- `f1_data.csv` dependency on startup
- `prediction_service` alias anti-pattern
