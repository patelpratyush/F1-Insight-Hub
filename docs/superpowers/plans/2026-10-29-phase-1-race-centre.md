# Phase 1: Data and Live Race Centre Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the first real product: calendar, standings, results, driver and team profiles, weather, command palette search, and a live race centre whose timing tower updates over SSE with under 5 s lag.

**Architecture:** The worker ingests Jolpica (calendar, results, constructor standings), Open-Meteo (weather) and OpenF1 (live) into Postgres and Redis. A pure reducer in `f1_core.live` turns normalised live events into timing-tower state. The api exposes typed read endpoints and an SSE stream with resume. The web app uses server components for static data and a client hook for live data.

**Tech Stack:** Everything from Phase 0, plus `sse-starlette` (api), `httpx` streaming (worker), Redis Streams, Open-Meteo API, OpenF1 API.

**Spec:** `docs/superpowers/specs/2026-10-29-f1-insight-hub-rewrite-design.md` (sections 3 to 5). Depends on: Phase 0 complete and merged.

## Global Constraints

- All Phase 0 constraints apply (strict types, `/v1`, problem+json, idempotent upserts, no upstream calls in request path).
- Live data is labelled "Unofficial, community data (OpenF1)". The UI shows a visible "Updated Xs ago" and a stale banner when the stream is silent for more than 15 s during a live session.
- Live-data lag budget: under 5 s from OpenF1 to browser.
- SSE: heartbeat every 15 s, `Last-Event-ID` resume, at most 3 concurrent streams per IP, at most 500 per api instance.
- Table name for sessions is `race_sessions` (the `sessions` name is used by auth).

## Review Focus

1. A race weekend has no sprint, or a session was cancelled or red-flagged: session list and results handle missing and `status="cancelled"` sessions without errors. (Task 2, Task 5)
2. A driver changes team mid-season (for example a replacement driver): profile and standings attribute points to the correct team per round. (Task 1, Task 5)
3. OpenF1 is down or returns an empty feed at session start: the stream emits `status: waiting`, the UI shows "Waiting for live data" and never a blank tower. (Task 8, Task 10)
4. Client reconnects with `Last-Event-ID` after a drop: no duplicate or missing events. (Task 8)
5. A driver retires or is in the pit lane: the tower shows `OUT` or `PIT` and does not break ordering. (Task 7)
6. Gap values arrive as `"+1 LAP"` or `null` instead of seconds: reducer and UI render them verbatim without NaN. (Task 7)
7. Timezones: session start times display in the viewer's local time while the API returns UTC. (Task 9)

---

## File Structure

```
packages/db-py/alembic/versions/0002_race_centre.py
packages/db-py/src/f1_db/models/{circuits.py,sessions.py,weather.py,constructors.py,live.py}
packages/core-py/src/f1_core/live/{__init__,events,state,reducer}.py
packages/core-py/tests/live/test_reducer.py
apps/worker/src/f1_worker/sources/{openmeteo.py,openf1.py}
apps/worker/src/f1_worker/jobs/{calendar,results,constructors,weather,live_poll,live_flush}.py
apps/worker/src/f1_worker/scheduling.py
apps/api/src/f1_api/routers/{calendar,races,drivers,teams,search,live}.py
apps/api/src/f1_api/services/{calendar,races,drivers,teams,search,live}.py
apps/api/src/f1_api/schemas/{calendar,races,drivers,teams,search,live}.py
apps/web/src/app/{page.tsx,calendar,races/[season]/[round],drivers/[ref],teams/[ref],live}/...
apps/web/src/components/{next-race-card,calendar-grid,race-results,driver-header,live/*}
apps/web/src/hooks/use-live-session.ts
apps/web/src/components/command-palette-host.tsx
```

---

### Task 1: Schema for calendar, sessions, weather, constructors and live

**Files:**
- Create: `packages/db-py/src/f1_db/models/{circuits,sessions,weather,constructors,live}.py`, `packages/db-py/alembic/versions/0002_race_centre.py`
- Modify: `packages/db-py/src/f1_db/models/{__init__,reference}.py`
- Test: `packages/db-py/tests/test_schema_phase1.py`

**Interfaces:**
- Produces models: `Circuit(id, ref, name, locality, country, lat: float, lon: float)`, `RaceSession(id, race_id, type: str, starts_at: datetime, ends_at: datetime | None, status: str, openf1_session_key: int | None)` unique on `(race_id, type)`, `WeatherSample(id, race_id, observed_at, air_temp_c, track_temp_c, humidity, wind_kph, rain_probability, source)` unique on `(race_id, observed_at, source)`, `ConstructorStanding(id, season_id, round, team_id, position, points: Decimal, wins)`, `DriverTeamStint(id, season_id, driver_id, team_id, from_round, to_round | None)`, `LapRecord(id, race_session_id, driver_id, lap_number, lap_time_ms, s1_ms, s2_ms, s3_ms, is_pit_out, compound)` unique on `(race_session_id, driver_id, lap_number)`, `PitStop(id, race_session_id, driver_id, lap_number, duration_ms)`, `Stint(id, race_session_id, driver_id, stint_number, compound, lap_start, lap_end)`.
- `Race` gains `circuit_id: UUID FK circuits.id nullable` and `start_utc` is derived from sessions (not stored).

- [ ] **Step 1: Write the failing test**

```python
# packages/db-py/tests/test_schema_phase1.py
from decimal import Decimal
from datetime import UTC, datetime

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from f1_db.models import Circuit, Race, RaceSession, Season
from f1_db.session import make_session_factory

EXPECTED = {"circuits", "race_sessions", "weather_samples", "constructor_standings",
            "driver_team_stints", "laps", "pit_stops", "stints"}


async def test_tables_exist(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert EXPECTED <= names


async def test_race_session_unique_per_race_and_type(engine: AsyncEngine) -> None:
    factory = make_session_factory(engine)
    async with factory() as s:
        season = Season(year=2098)
        circuit = Circuit(ref="c1", name="C", locality="L", country="X", lat=1.0, lon=2.0)
        s.add_all([season, circuit])
        await s.flush()
        race = Race(season_id=season.id, round=1, name="GP", circuit_name="C",
                    race_date=datetime(2098, 3, 1).date(), circuit_id=circuit.id)
        s.add(race)
        await s.flush()
        when = datetime(2098, 3, 1, 14, tzinfo=UTC)
        s.add(RaceSession(race_id=race.id, type="R", starts_at=when, status="scheduled"))
        await s.commit()
        s.add(RaceSession(race_id=race.id, type="R", starts_at=when, status="scheduled"))
        with pytest.raises(IntegrityError):
            await s.commit()
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/db-py/tests/test_schema_phase1.py -v`
Expected: FAIL (`ImportError: Circuit`).

- [ ] **Step 3: Implement models**

```python
# packages/db-py/src/f1_db/models/circuits.py
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class Circuit(IdMixin, IngestedMixin, Base):
    __tablename__ = "circuits"
    ref: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    locality: Mapped[str]
    country: Mapped[str]
    lat: Mapped[float]
    lon: Mapped[float]
```

```python
# packages/db-py/src/f1_db/models/sessions.py
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class RaceSession(IdMixin, IngestedMixin, Base):
    __tablename__ = "race_sessions"
    __table_args__ = (UniqueConstraint("race_id", "type"),)
    race_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("races.id"), index=True)
    type: Mapped[str]  # FP1 FP2 FP3 SQ SPRINT Q R
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(default="scheduled")  # scheduled live finished cancelled
    openf1_session_key: Mapped[int | None]


class LapRecord(IdMixin, IngestedMixin, Base):
    __tablename__ = "laps"
    __table_args__ = (UniqueConstraint("race_session_id", "driver_id", "lap_number"),)
    race_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("race_sessions.id"), index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    lap_number: Mapped[int]
    lap_time_ms: Mapped[int | None]
    s1_ms: Mapped[int | None]
    s2_ms: Mapped[int | None]
    s3_ms: Mapped[int | None]
    is_pit_out: Mapped[bool] = mapped_column(default=False)
    compound: Mapped[str | None]


class PitStop(IdMixin, IngestedMixin, Base):
    __tablename__ = "pit_stops"
    __table_args__ = (UniqueConstraint("race_session_id", "driver_id", "lap_number"),)
    race_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("race_sessions.id"), index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    lap_number: Mapped[int]
    duration_ms: Mapped[int | None]


class Stint(IdMixin, IngestedMixin, Base):
    __tablename__ = "stints"
    __table_args__ = (UniqueConstraint("race_session_id", "driver_id", "stint_number"),)
    race_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("race_sessions.id"), index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    stint_number: Mapped[int]
    compound: Mapped[str]
    lap_start: Mapped[int]
    lap_end: Mapped[int | None]
```

```python
# packages/db-py/src/f1_db/models/weather.py
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin


class WeatherSample(IdMixin, Base):
    __tablename__ = "weather_samples"
    __table_args__ = (UniqueConstraint("race_id", "observed_at", "source"),)
    race_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("races.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    air_temp_c: Mapped[float | None]
    track_temp_c: Mapped[float | None]
    humidity: Mapped[float | None]
    wind_kph: Mapped[float | None]
    rain_probability: Mapped[float | None]
    source: Mapped[str]
```

```python
# packages/db-py/src/f1_db/models/constructors.py
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class ConstructorStanding(IdMixin, IngestedMixin, Base):
    __tablename__ = "constructor_standings"
    __table_args__ = (UniqueConstraint("season_id", "round", "team_id"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"), index=True)
    round: Mapped[int]
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int]
    points: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    wins: Mapped[int]


class DriverTeamStint(IdMixin, IngestedMixin, Base):
    __tablename__ = "driver_team_stints"
    __table_args__ = (UniqueConstraint("season_id", "driver_id", "team_id", "from_round"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    from_round: Mapped[int]
    to_round: Mapped[int | None]
```

In `reference.py` add to `Race`: `circuit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("circuits.id"))`. Export all new classes in `models/__init__.py` (`Circuit`, `RaceSession`, `LapRecord`, `PitStop`, `Stint`, `WeatherSample`, `ConstructorStanding`, `DriverTeamStint`). Delete `models/live.py` from the file list (live state lives in Redis).

- [ ] **Step 4: Generate migration, run, commit**

```bash
export DATABASE_URL=postgresql+asyncpg://f1:f1@localhost:5432/f1
uv run --directory packages/db-py alembic revision --autogenerate -m "race centre" --rev-id 0002
uv run pytest packages/db-py/tests -v
git add -A && git commit -m "feat(db): add circuits, sessions, weather, constructors, laps schema"
```

Expected: migration adds the eight tables and `races.circuit_id`; tests pass.

---

### Task 2: Calendar and sessions ingestion

**Files:**
- Modify: `apps/worker/src/f1_worker/sources/jolpica.py`
- Create: `apps/worker/src/f1_worker/jobs/calendar.py`, `apps/worker/tests/fixtures/calendar_2025.json`
- Test: `apps/worker/tests/test_calendar_job.py`

**Interfaces:**
- Produces: `ParsedRace(round, name, circuit_ref, circuit_name, locality, country, lat, lon, race_date, sessions: dict[str, datetime])` where `sessions` keys are in `{"FP1","FP2","FP3","SQ","SPRINT","Q","R"}` (only those present). `JolpicaClient.calendar(year) -> list[ParsedRace]`. `ingest_calendar(session_factory, client, year) -> int` upserts `Season`, `Circuit`, `Race`, `RaceSession`, recording job `calendar`.

- [ ] **Step 1: Write the fixture and failing tests**

Fixture `calendar_2025.json` (trimmed to two rounds; round 2 is a sprint weekend so it has `SprintQualifying` and `Sprint`, round 1 does not):

```json
{
  "MRData": {"RaceTable": {"season": "2025", "Races": [
    {"season": "2025", "round": "1", "raceName": "Australian Grand Prix",
     "Circuit": {"circuitId": "albert_park", "circuitName": "Albert Park Grand Prix Circuit",
       "Location": {"lat": "-37.8497", "long": "144.968", "locality": "Melbourne", "country": "Australia"}},
     "date": "2025-03-16", "time": "04:00:00Z",
     "FirstPractice": {"date": "2025-03-14", "time": "01:30:00Z"},
     "SecondPractice": {"date": "2025-03-14", "time": "05:00:00Z"},
     "ThirdPractice": {"date": "2025-03-15", "time": "01:30:00Z"},
     "Qualifying": {"date": "2025-03-15", "time": "05:00:00Z"}},
    {"season": "2025", "round": "2", "raceName": "Chinese Grand Prix",
     "Circuit": {"circuitId": "shanghai", "circuitName": "Shanghai International Circuit",
       "Location": {"lat": "31.3389", "long": "121.22", "locality": "Shanghai", "country": "China"}},
     "date": "2025-03-23", "time": "07:00:00Z",
     "FirstPractice": {"date": "2025-03-21", "time": "03:30:00Z"},
     "SprintQualifying": {"date": "2025-03-21", "time": "07:30:00Z"},
     "Sprint": {"date": "2025-03-22", "time": "03:00:00Z"},
     "Qualifying": {"date": "2025-03-22", "time": "07:00:00Z"}}
  ]}}
}
```

```python
# apps/worker/tests/test_calendar_job.py
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_db.models import Race, RaceSession
from f1_worker.jobs.calendar import ingest_calendar
from f1_worker.sources.jolpica import JolpicaClient

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "calendar_2025.json").read_text())
URL = "https://api.jolpi.ca/ergast/f1/2025.json"


@pytest.fixture(autouse=True)
async def clean(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        await s.execute(text("truncate race_sessions, races, circuits, seasons cascade"))
        await s.commit()


@respx.mock
async def test_parses_sessions_per_weekend_format() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    races = await JolpicaClient().calendar(2025)
    assert set(races[0].sessions) == {"FP1", "FP2", "FP3", "Q", "R"}
    assert set(races[1].sessions) == {"FP1", "SQ", "SPRINT", "Q", "R"}
    assert races[0].sessions["R"] == datetime(2025, 3, 16, 4, 0, tzinfo=UTC)


@respx.mock
async def test_ingest_is_idempotent(session_factory: async_sessionmaker[AsyncSession]) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    assert await ingest_calendar(session_factory, JolpicaClient(), 2025) == 2
    assert await ingest_calendar(session_factory, JolpicaClient(), 2025) == 2
    async with session_factory() as s:
        races = (await s.execute(select(func.count()).select_from(Race))).scalar_one()
        sessions = (await s.execute(select(func.count()).select_from(RaceSession))).scalar_one()
    assert races == 2 and sessions == 9


@respx.mock
async def test_empty_calendar_is_noop(session_factory: async_sessionmaker[AsyncSession]) -> None:
    empty = {"MRData": {"RaceTable": {"season": "2030", "Races": []}}}
    respx.get("https://api.jolpi.ca/ergast/f1/2030.json").mock(return_value=httpx.Response(200, json=empty))
    assert await ingest_calendar(session_factory, JolpicaClient(), 2030) == 0
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest apps/worker/tests/test_calendar_job.py -v`
Expected: FAIL (`AttributeError: calendar`).

- [ ] **Step 3: Implement the parser and job**

Add to `jolpica.py`:

```python
from datetime import UTC, date, datetime

SESSION_KEYS = {
    "FirstPractice": "FP1", "SecondPractice": "FP2", "ThirdPractice": "FP3",
    "SprintQualifying": "SQ", "SprintShootout": "SQ", "Sprint": "SPRINT", "Qualifying": "Q",
}


@dataclass(frozen=True)
class ParsedRace:
    round: int
    name: str
    circuit_ref: str
    circuit_name: str
    locality: str
    country: str
    lat: float
    lon: float
    race_date: date
    sessions: dict[str, datetime]


def _dt(block: dict[str, str]) -> datetime:
    time = block.get("time", "00:00:00Z").replace("Z", "+00:00")
    return datetime.fromisoformat(f"{block['date']}T{time}").astimezone(UTC)
```

and the method on `JolpicaClient`:

```python
    async def calendar(self, year: int) -> list[ParsedRace]:
        data = await self._get_json(f"/{year}.json")
        out: list[ParsedRace] = []
        for r in data["MRData"]["RaceTable"]["Races"]:
            circuit, loc = r["Circuit"], r["Circuit"]["Location"]
            sessions = {key: _dt(r[name]) for name, key in SESSION_KEYS.items() if name in r}
            sessions["R"] = _dt({"date": r["date"], "time": r.get("time", "00:00:00Z")})
            out.append(ParsedRace(
                round=int(r["round"]), name=r["raceName"], circuit_ref=circuit["circuitId"],
                circuit_name=circuit["circuitName"], locality=loc["locality"], country=loc["country"],
                lat=float(loc["lat"]), lon=float(loc["long"]),
                race_date=date.fromisoformat(r["date"]), sessions=sessions,
            ))
        return out
```

```python
# apps/worker/src/f1_worker/jobs/calendar.py
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import Circuit, Race, RaceSession, Season
from f1_worker.runs import record_run
from f1_worker.sources.jolpica import JolpicaClient

SOURCE = "jolpica"


async def ingest_calendar(
    session_factory: async_sessionmaker[AsyncSession], client: JolpicaClient, year: int
) -> int:
    async with record_run(session_factory, "calendar") as run:
        races = await client.calendar(year)
        if not races:
            return 0
        async with session_factory() as s:
            await s.execute(insert(Season).values(id=uuid7(), year=year)
                            .on_conflict_do_nothing(index_elements=["year"]))
            season_id = (await s.execute(select(Season.id).where(Season.year == year))).scalar_one()
            for r in races:
                await s.execute(insert(Circuit).values(
                    id=uuid7(), ref=r.circuit_ref, name=r.circuit_name, locality=r.locality,
                    country=r.country, lat=r.lat, lon=r.lon, source=SOURCE, ingested_at=utcnow(),
                ).on_conflict_do_update(index_elements=["ref"], set_={"name": r.circuit_name}))
                circuit_id = (await s.execute(select(Circuit.id).where(Circuit.ref == r.circuit_ref))).scalar_one()
                await s.execute(insert(Race).values(
                    id=uuid7(), season_id=season_id, round=r.round, name=r.name,
                    circuit_name=r.circuit_name, race_date=r.race_date, circuit_id=circuit_id,
                    source=SOURCE, ingested_at=utcnow(),
                ).on_conflict_do_update(
                    index_elements=["season_id", "round"],
                    set_={"name": r.name, "race_date": r.race_date, "circuit_id": circuit_id},
                ))
                race_id = (await s.execute(select(Race.id).where(
                    Race.season_id == season_id, Race.round == r.round))).scalar_one()
                for stype, starts in r.sessions.items():
                    await s.execute(insert(RaceSession).values(
                        id=uuid7(), race_id=race_id, type=stype, starts_at=starts,
                        status="scheduled", source=SOURCE, ingested_at=utcnow(),
                    ).on_conflict_do_update(
                        index_elements=["race_id", "type"], set_={"starts_at": starts}))
            await s.commit()
        run.rows = len(races)
        return len(races)
```

- [ ] **Step 4: Run to confirm pass and commit**

Run: `uv run pytest apps/worker/tests/test_calendar_job.py -v`
Expected: 3 passed.

```bash
git add -A && git commit -m "feat(worker): ingest season calendar with sessions"
```

---

### Task 3: Race results, constructor standings and stints ingestion

**Files:**
- Modify: `apps/worker/src/f1_worker/sources/jolpica.py`
- Create: `apps/worker/src/f1_worker/jobs/{results,constructors}.py`, fixtures `race_results_2025_1.json`, `constructor_standings_2025.json`
- Test: `apps/worker/tests/test_results_job.py`, `test_constructors_job.py`

**Interfaces:**
- Produces: `ParsedResult(session_type: str, driver_ref, team_ref, position: int | None, grid: int | None, status: str, points: Decimal, time_ms: int | None, driver fields..., team fields...)`; `JolpicaClient.results(year, round) -> list[ParsedResult]` (race), `qualifying(year, round)`, `sprint(year, round)`. `ingest_results(session_factory, client, year, round) -> int` writes `SessionResult` (unique `race_id, session_type, driver_id`) and maintains `DriverTeamStint` (opens a new stint when a driver's team differs from the open stint, closing the old one with `to_round = round - 1`). `ingest_constructor_standings(session_factory, client, year) -> int`.

- [ ] **Step 1: Write the failing tests** (include a mid-season team change)

```python
# apps/worker/tests/test_results_job.py  (key tests)
async def test_team_change_creates_new_stint(session_factory, ...):
    # round 5: driver "lawson" at red_bull; round 6 result lists him at racing_bulls
    await ingest_results(session_factory, client_r5, 2025, 5)
    await ingest_results(session_factory, client_r6, 2025, 6)
    stints = (await s.execute(select(DriverTeamStint).where(...order_by(DriverTeamStint.from_round)))).scalars().all()
    assert [(st.from_round, st.to_round) for st in stints] == [(1, 5), (6, None)]

async def test_results_idempotent_and_dnf_has_null_position(...):
    # a retired driver has status "Retired" and position kept as classified position or None
    ...
async def test_fractional_sprint_points_preserved(...):
    # sprint half points e.g. "0.5" stored as Decimal("0.50")
```

Write the full tests with fixtures following the exact pattern of Task 2: `respx.mock` against `https://api.jolpi.ca/ergast/f1/2025/5/results.json`, `.../2025/6/results.json`; assert counts using `select(func.count())`. The fixtures contain three drivers each (one DNF with `"status": "Retired"`, `"positionText": "R"`, and one sprint-style `"points": "0.5"` fixture for the fractional test).

- [ ] **Step 2: Run to confirm failure**, then implement

Implement `JolpicaClient.results/qualifying/sprint` by fetching `/{year}/{round}/results.json`, `/qualifying.json`, `/sprint.json`. Parse rows from `MRData.RaceTable.Races[0].Results` (or `QualifyingResults`, `SprintResults`). Position rule: `int(item["position"])` when `positionText` is numeric, else `None`. `time_ms` from `Time.millis` if present. Return `[]` when `Races` is empty.

`ingest_results` upserts reference rows via the same helpers as Task 11 of Phase 0 (extract `upsert_driver` and `upsert_team` into `f1_worker/jobs/_upserts.py` and make `standings.py` use them), upserts `SessionResult`, then runs:

```python
async def sync_stint(s: AsyncSession, season_id, driver_id, team_id, rnd: int) -> None:
    open_stint = (await s.execute(select(DriverTeamStint).where(
        DriverTeamStint.season_id == season_id, DriverTeamStint.driver_id == driver_id,
        DriverTeamStint.to_round.is_(None)))).scalar_one_or_none()
    if open_stint is None:
        s.add(DriverTeamStint(season_id=season_id, driver_id=driver_id, team_id=team_id,
                              from_round=1 if rnd <= 1 else rnd, source=SOURCE))
    elif open_stint.team_id != team_id:
        open_stint.to_round = rnd - 1
        s.add(DriverTeamStint(season_id=season_id, driver_id=driver_id, team_id=team_id,
                              from_round=rnd, source=SOURCE))
```

For the first-ever stint use `from_round=1` when backfilling from round 1 (the test above ingests round 1..5 in a loop in its setup; the assertion `(1, 5), (6, None)` follows from ingesting rounds 1 to 6 in order).

`ingest_constructor_standings` mirrors Phase 0 `ingest_driver_standings` against `/{year}/constructorStandings.json` and `ConstructorStanding`.

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest apps/worker/tests -v`
Expected: all pass.

```bash
git add -A && git commit -m "feat(worker): ingest results, constructor standings and team stints"
```

---

### Task 4: Weather ingestion (Open-Meteo)

**Files:**
- Create: `apps/worker/src/f1_worker/sources/openmeteo.py`, `apps/worker/src/f1_worker/jobs/weather.py`, fixture `openmeteo_albert_park.json`
- Test: `apps/worker/tests/test_weather_job.py`

**Interfaces:**
- Produces: `OpenMeteoClient.forecast(lat: float, lon: float, start: date, end: date) -> list[WeatherPoint]` with `WeatherPoint(observed_at: datetime, air_temp_c, humidity, wind_kph, rain_probability)`. `ingest_weather(session_factory, client, race_id) -> int` stores hourly points between Friday and Sunday of the weekend. Track temperature is `None` from this source (OpenF1 provides it live).

- [ ] **Step 1: Write the failing tests**

```python
@respx.mock
async def test_parses_hourly_points() -> None:
    respx.get(url__startswith="https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=FIXTURE))
    pts = await OpenMeteoClient().forecast(-37.8497, 144.968, date(2025, 3, 14), date(2025, 3, 16))
    assert pts[0].observed_at.tzinfo is not None
    assert pts[0].rain_probability == 20.0

@respx.mock
async def test_null_values_become_none(...):
    # fixture contains "precipitation_probability": [null, 10] -> first point has None
    ...

@respx.mock
async def test_ingest_weather_is_idempotent(session_factory) -> None: ...
```

Fixture shape (`hourly`): `{"time": ["2025-03-14T00:00", ...], "temperature_2m": [...], "relative_humidity_2m": [...], "wind_speed_10m": [...], "precipitation_probability": [...]}` with `timezone=UTC` requested.

- [ ] **Step 2: Implement**

```python
class OpenMeteoClient:
    URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(timeout=10.0)
        self.breaker = CircuitBreaker(5, 60)

    async def forecast(self, lat: float, lon: float, start: date, end: date) -> list[WeatherPoint]:
        params = {
            "latitude": lat, "longitude": lon, "timezone": "UTC",
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation_probability",
        }

        async def go() -> dict[str, Any]:
            resp = await self.client.get(self.URL, params=params)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data

        h = (await self.breaker.call(go))["hourly"]
        return [
            WeatherPoint(
                observed_at=datetime.fromisoformat(t).replace(tzinfo=UTC),
                air_temp_c=h["temperature_2m"][i], humidity=h["relative_humidity_2m"][i],
                wind_kph=h["wind_speed_10m"][i], rain_probability=h["precipitation_probability"][i],
            )
            for i, t in enumerate(h["time"])
        ]
```

`ingest_weather` loads the `Race` and its `Circuit`, requests `race_date - 2 days` to `race_date`, upserts into `weather_samples` with `ON CONFLICT (race_id, observed_at, source) DO UPDATE`, `source="open-meteo"`.

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest apps/worker/tests/test_weather_job.py -v`
Expected: pass.

```bash
git add -A && git commit -m "feat(worker): ingest weekend weather from open-meteo"
```

---

### Task 5: Read API: calendar, race, results, drivers, teams

**Files:**
- Create: `apps/api/src/f1_api/{schemas,services,routers}/{calendar,races,drivers,teams}.py`
- Modify: `apps/api/src/f1_api/main.py`
- Test: `apps/api/tests/test_{calendar,races,drivers,teams}_api.py`

**Interfaces (all public, rate limited 120 per minute, cache header `Cache-Control: public, max-age=60, stale-while-revalidate=300` and a weak `ETag` computed from the JSON body):**
- `GET /v1/calendar?season=` returns `list[RaceSummary]`: `{season, round, name, circuit: {ref,name,locality,country,lat,lon}, race_date, sessions: [{type, starts_at, status}]}`.
- `GET /v1/races/{season}/{round}` returns `RaceDetail` = `RaceSummary` + `weather: list[WeatherOut]` + `results: {R: list[ResultRow], Q: [...], SPRINT: [...]}`; `404` problem if unknown.
- `GET /v1/drivers/{ref}` returns `DriverProfile`: identity, `seasons: [{year, team, position, points, wins}]`, `recent_results: list[ResultRow]` (last 10), `team_history: [{team, from_round, to_round, season}]`.
- `GET /v1/teams/{ref}` returns `TeamProfile`: identity, `color` (hex from `team_colors` map in `f1_core.teams`), `drivers`, `standings_history`.
- `GET /v1/standings/constructors?season=`.
- `ResultRow = {position: int | null, grid: int | null, status: str, points: float, time_ms: int | null, driver: DriverRef, team: TeamRef}`.

- [ ] **Step 1: Write the failing tests**

Write one seed helper `apps/api/tests/seed.py` with `async seed_season(pg_url) -> SeedIds` creating season 2031 with 2 circuits, 3 races (round 2 sprint weekend, round 3 with a `cancelled` Q session), 3 drivers (one changes team at round 2), results for rounds 1 to 2, constructor standings and weather. Then tests:

```python
async def test_calendar_lists_races_in_round_order(client, seeded): 
    rows = (await client.get("/v1/calendar", params={"season": 2031})).json()
    assert [r["round"] for r in rows] == [1, 2, 3]

async def test_sprint_weekend_has_sprint_session_and_cancelled_is_reported(client, seeded):
    rows = (await client.get("/v1/calendar", params={"season": 2031})).json()
    assert "SPRINT" in {s["type"] for s in rows[1]["sessions"]}
    assert {"type": "Q", "status": "cancelled"}.items() <= next(s for s in rows[2]["sessions"] if s["type"] == "Q").items()

async def test_race_detail_404_problem(client, seeded):
    r = await client.get("/v1/races/2031/99")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/problem+json")

async def test_driver_profile_has_team_history_in_order(client, seeded):
    body = (await client.get("/v1/drivers/swapper")).json()
    assert [(h["team"], h["from_round"]) for h in body["team_history"]] == [("Alpha", 1), ("Beta", 2)]

async def test_etag_returns_304_on_match(client, seeded):
    first = await client.get("/v1/calendar", params={"season": 2031})
    second = await client.get("/v1/calendar", params={"season": 2031},
                              headers={"If-None-Match": first.headers["etag"]})
    assert second.status_code == 304

async def test_dnf_row_has_null_position_and_status(client, seeded): ...
async def test_team_profile_includes_color_and_drivers(client, seeded): ...
```

- [ ] **Step 2: Run to confirm failure**, then implement

Implement a reusable `cached_json` helper in `f1_api/http_cache.py`:

```python
import hashlib
import json

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

CACHE = "public, max-age=60, stale-while-revalidate=300"


def cached_json(request: Request, payload: object) -> Response:
    body = json.dumps(jsonable_encoder(payload), separators=(",", ":"), sort_keys=True)
    etag = 'W/"' + hashlib.sha256(body.encode()).hexdigest()[:24] + '"'
    headers = {"ETag": etag, "Cache-Control": CACHE}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(json.loads(body), headers=headers)
```

Services return Pydantic models; routers wrap them with `cached_json(request, result)` and set `response_model` for OpenAPI via `responses={200: {"model": ...}}` (use `operation_id` names `getCalendar`, `getRace`, `getDriver`, `getTeam`, `getConstructorStandings`). Raise `ProblemError(404, "Not found", "...")` for missing resources. Add `f1_core/teams.py` with `TEAM_COLORS: dict[str, str]` keyed by Jolpica constructor ref (`mclaren: "#FF8000"`, `red_bull: "#3671C6"`, `ferrari: "#E8002D"`, `mercedes: "#27F4D2"`, ...) and a `team_color(ref) -> str` that falls back to `#E10600`. Test `team_color("unknown") == "#E10600"` in `packages/core-py/tests/test_teams.py`.

Run `pnpm contract` and commit the regenerated contract with the code.

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest apps/api packages/core-py -v`
Expected: all pass.

```bash
git add -A && git commit -m "feat(api): add calendar, race, driver, team and constructor endpoints"
```

---

### Task 6: Search endpoint

**Files:**
- Create: `apps/api/src/f1_api/{schemas,services,routers}/search.py`
- Test: `apps/api/tests/test_search_api.py`

**Interfaces:**
- Produces: `GET /v1/search?q=<2..64 chars>` returning `list[SearchHit]` where `SearchHit = {kind: "driver" | "team" | "race", id: str, label: str, hint: str | None, href: str}`; at most 20 hits, ranked: exact prefix first, then substring; accents and case ignored. Uses `unaccent` and `ILIKE`. Enable the extension in migration `0003_search.py` (`CREATE EXTENSION IF NOT EXISTS unaccent`) and add `pg_trgm` GIN indexes on `drivers(family_name, given_name)`, `teams(name)`, `races(name)`.

- [ ] **Step 1: Write the failing tests**

```python
async def test_finds_driver_ignoring_case_and_accents(client, seeded):
    hits = (await client.get("/v1/search", params={"q": "perez"})).json()   # seeded "Pérez"
    assert hits[0]["kind"] == "driver" and hits[0]["href"] == "/drivers/perez"

async def test_prefix_ranks_before_substring(client, seeded): ...

@pytest.mark.parametrize("q", ["", "a", "x" * 65])
async def test_bad_query_length_is_422(client, q): ...

async def test_wildcards_are_escaped(client, seeded):
    hits = (await client.get("/v1/search", params={"q": "%%"})).json()
    assert hits == []
```

- [ ] **Step 2: Implement and commit**

Escape `%`, `_` and `\` in the user query before building `ILIKE` patterns (`q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")` with `escape="\\"`). Compose three queries (drivers, teams, races), tag results with a rank (0 prefix, 1 substring), merge, sort by `(rank, label)`, cap at 20. Rate limit 60 per minute per IP.

Run: `uv run pytest apps/api/tests/test_search_api.py -v` (Expected: pass), then `pnpm contract`.

```bash
git add -A && git commit -m "feat(api): add accent-insensitive search endpoint"
```

---

### Task 7: Live timing reducer (pure domain logic)

**Files:**
- Create: `packages/core-py/src/f1_core/live/{__init__,events,state,reducer}.py`
- Test: `packages/core-py/tests/live/test_reducer.py`

**Interfaces:**
- Produces:
  - `LiveEvent` (frozen dataclass): `seq: int`, `ts: datetime`, `kind: Literal["position","lap","interval","stint","pit","flag","weather","status"]`, `driver_number: int | None`, `data: Mapping[str, object]`.
  - `DriverTiming`: `number, position: int | None, code: str | None, last_lap_ms: int | None, best_lap_ms: int | None, gap_to_leader: str | None, interval: str | None, compound: str | None, tyre_age_laps: int | None, in_pit: bool, retired: bool, sectors: tuple[SectorColor, SectorColor, SectorColor]`, with `SectorColor = Literal["purple","green","yellow","none"]`.
  - `TimingState`: `drivers: dict[int, DriverTiming]`, `flag: str`, `lap: int | None`, `session_best_lap_ms: int | None`, `session_best_sectors_ms: tuple[int | None, int | None, int | None]`, `last_seq: int`, `status: Literal["waiting","live","finished"]`.
  - `apply_event(state: TimingState, event: LiveEvent) -> TimingState` (pure, returns a new state; ignores events with `seq <= state.last_seq`).
  - `ordered_tower(state) -> list[DriverTiming]`: sorted by `position`, with drivers lacking a position last (by number), retired drivers last.

- [ ] **Step 1: Write the failing tests**

```python
# packages/core-py/tests/live/test_reducer.py
from datetime import UTC, datetime

from f1_core.live.events import LiveEvent
from f1_core.live.reducer import apply_event, ordered_tower
from f1_core.live.state import TimingState

T0 = datetime(2025, 3, 16, 4, 0, tzinfo=UTC)


def ev(seq: int, kind: str, number: int | None = None, **data: object) -> LiveEvent:
    return LiveEvent(seq=seq, ts=T0, kind=kind, driver_number=number, data=data)  # type: ignore[arg-type]


def test_position_events_order_the_tower() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "position", 4, position=2))
    s = apply_event(s, ev(2, "position", 1, position=1))
    assert [d.number for d in ordered_tower(s)] == [1, 4]


def test_stale_or_duplicate_seq_is_ignored() -> None:
    s = apply_event(TimingState.empty(), ev(5, "position", 1, position=1))
    again = apply_event(s, ev(5, "position", 1, position=9))
    older = apply_event(s, ev(3, "position", 1, position=9))
    assert again.drivers[1].position == 1 and older.drivers[1].position == 1


def test_overall_best_lap_is_purple_and_personal_best_green() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "lap", 1, lap_time_ms=90000, sectors_ms=[30000, 30000, 30000]))
    s = apply_event(s, ev(2, "lap", 4, lap_time_ms=91000, sectors_ms=[30500, 30500, 30000]))
    assert s.drivers[1].sectors == ("purple", "purple", "purple")
    assert s.drivers[4].sectors == ("none", "none", "purple") or s.drivers[4].sectors[2] == "yellow"
    s = apply_event(s, ev(3, "lap", 4, lap_time_ms=90500, sectors_ms=[30200, 30200, 30100]))
    assert s.drivers[4].best_lap_ms == 90500
    assert s.drivers[4].sectors[0] == "green"


def test_gap_strings_are_kept_verbatim() -> None:
    s = apply_event(TimingState.empty(), ev(1, "interval", 7, gap_to_leader="+1 LAP", interval=None))
    assert s.drivers[7].gap_to_leader == "+1 LAP"
    assert s.drivers[7].interval is None


def test_retired_driver_sorts_last_and_pit_flag_toggles() -> None:
    s = TimingState.empty()
    s = apply_event(s, ev(1, "position", 1, position=1))
    s = apply_event(s, ev(2, "position", 2, position=2))
    s = apply_event(s, ev(3, "status", 1, retired=True))
    s = apply_event(s, ev(4, "pit", 2, in_pit=True))
    assert [d.number for d in ordered_tower(s)] == [2, 1]
    assert s.drivers[2].in_pit is True


def test_flag_and_status_events() -> None:
    s = apply_event(TimingState.empty(), ev(1, "flag", None, flag="YELLOW"))
    assert s.flag == "YELLOW"
    s = apply_event(s, ev(2, "status", None, session="live"))
    assert s.status == "live"


def test_unknown_driver_in_lap_event_creates_driver() -> None:
    s = apply_event(TimingState.empty(), ev(1, "lap", 99, lap_time_ms=95000, sectors_ms=[None, None, None]))
    assert 99 in s.drivers and s.drivers[99].last_lap_ms == 95000


def test_reducer_is_pure() -> None:
    s = TimingState.empty()
    apply_event(s, ev(1, "position", 1, position=1))
    assert s.drivers == {}
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/core-py/tests/live -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

```python
# packages/core-py/src/f1_core/live/events.py
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Kind = Literal["position", "lap", "interval", "stint", "pit", "flag", "weather", "status"]


@dataclass(frozen=True)
class LiveEvent:
    seq: int
    ts: datetime
    kind: Kind
    driver_number: int | None
    data: Mapping[str, object]
```

```python
# packages/core-py/src/f1_core/live/state.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SectorColor = Literal["purple", "green", "yellow", "none"]
Sectors = tuple[SectorColor, SectorColor, SectorColor]
NONE3: Sectors = ("none", "none", "none")


@dataclass(frozen=True)
class DriverTiming:
    number: int
    position: int | None = None
    code: str | None = None
    last_lap_ms: int | None = None
    best_lap_ms: int | None = None
    best_sectors_ms: tuple[int | None, int | None, int | None] = (None, None, None)
    gap_to_leader: str | None = None
    interval: str | None = None
    compound: str | None = None
    tyre_age_laps: int | None = None
    in_pit: bool = False
    retired: bool = False
    sectors: Sectors = NONE3


@dataclass(frozen=True)
class TimingState:
    drivers: dict[int, DriverTiming] = field(default_factory=dict)
    flag: str = "GREEN"
    lap: int | None = None
    session_best_lap_ms: int | None = None
    session_best_sectors_ms: tuple[int | None, int | None, int | None] = (None, None, None)
    last_seq: int = 0
    status: Literal["waiting", "live", "finished"] = "waiting"

    @staticmethod
    def empty() -> TimingState:
        return TimingState()
```

```python
# packages/core-py/src/f1_core/live/reducer.py
from dataclasses import replace
from typing import Any

from f1_core.live.events import LiveEvent
from f1_core.live.state import DriverTiming, SectorColor, TimingState


def _color(value: int | None, personal: int | None, overall: int | None) -> SectorColor:
    if value is None:
        return "none"
    if overall is not None and value <= overall:
        return "purple"
    if personal is not None and value <= personal:
        return "green"
    return "yellow"


def _apply_lap(state: TimingState, d: DriverTiming, data: Any) -> tuple[TimingState, DriverTiming]:
    lap_ms: int | None = data.get("lap_time_ms")
    secs: list[int | None] = list(data.get("sectors_ms", [None, None, None]))
    overall = list(state.session_best_sectors_ms)
    personal = list(d.best_sectors_ms)
    for i, v in enumerate(secs):
        if v is not None:
            overall[i] = v if overall[i] is None else min(overall[i], v)  # type: ignore[type-var]
    colors = tuple(
        _color(v, personal[i], overall[i]) for i, v in enumerate(secs)
    )
    for i, v in enumerate(secs):
        if v is not None:
            personal[i] = v if personal[i] is None else min(personal[i], v)  # type: ignore[type-var]
    best = d.best_lap_ms
    session_best = state.session_best_lap_ms
    if lap_ms is not None:
        best = lap_ms if best is None else min(best, lap_ms)
        session_best = lap_ms if session_best is None else min(session_best, lap_ms)
    d2 = replace(d, last_lap_ms=lap_ms if lap_ms is not None else d.last_lap_ms, best_lap_ms=best,
                 best_sectors_ms=tuple(personal), sectors=colors)  # type: ignore[arg-type]
    s2 = replace(state, session_best_lap_ms=session_best,
                 session_best_sectors_ms=tuple(overall))  # type: ignore[arg-type]
    return s2, d2


def apply_event(state: TimingState, event: LiveEvent) -> TimingState:
    if event.seq <= state.last_seq:
        return state
    state = replace(state, last_seq=event.seq)
    data = event.data
    if event.driver_number is None:
        if event.kind == "flag":
            return replace(state, flag=str(data["flag"]))
        if event.kind == "status" and "session" in data:
            return replace(state, status=data["session"])  # type: ignore[arg-type]
        if event.kind == "status" and "lap" in data:
            return replace(state, lap=int(data["lap"]))  # type: ignore[call-overload]
        return state
    drivers = dict(state.drivers)
    d = drivers.get(event.driver_number) or DriverTiming(number=event.driver_number)
    if event.kind == "position":
        d = replace(d, position=int(data["position"]))  # type: ignore[call-overload]
    elif event.kind == "interval":
        d = replace(d, gap_to_leader=data.get("gap_to_leader"), interval=data.get("interval"))  # type: ignore[arg-type]
    elif event.kind == "stint":
        d = replace(d, compound=data.get("compound"), tyre_age_laps=data.get("tyre_age_laps"))  # type: ignore[arg-type]
    elif event.kind == "pit":
        d = replace(d, in_pit=bool(data["in_pit"]))
    elif event.kind == "status":
        d = replace(d, retired=bool(data.get("retired", d.retired)))
    elif event.kind == "lap":
        state, d = _apply_lap(state, d, data)
    drivers[event.driver_number] = d
    return replace(state, drivers=drivers)


def ordered_tower(state: TimingState) -> list[DriverTiming]:
    def key(d: DriverTiming) -> tuple[int, int, int]:
        return (1 if d.retired else 0, d.position if d.position is not None else 10_000, d.number)

    return sorted(state.drivers.values(), key=key)
```

Note: the purple-then-yellow assertion in `test_overall_best_lap_is_purple_and_personal_best_green` accepts `("none","none","purple")` or yellow on the third sector, because driver 4's third sector (30000) ties the overall best (30000) so it is purple. Tighten it to `assert s.drivers[4].sectors == ("yellow", "yellow", "purple")` and confirm that passes with the implementation (first two sectors are slower than the overall best, and a first lap has no earlier personal best, so they are yellow).

- [ ] **Step 4: Run to confirm pass, 90% coverage, commit**

Run: `uv run pytest packages/core-py --cov=f1_core --cov-fail-under=90 -v`
Expected: all pass.

```bash
uv run mypy packages/core-py/src
git add -A && git commit -m "feat(core): add pure live timing reducer"
```

---

### Task 8: Live ingestion (OpenF1 to Redis) and SSE endpoint

**Files:**
- Create: `apps/worker/src/f1_worker/sources/openf1.py`, `apps/worker/src/f1_worker/jobs/live_poll.py`, `apps/api/src/f1_api/{schemas,services,routers}/live.py`
- Test: `apps/worker/tests/test_openf1.py`, `apps/worker/tests/test_live_poll.py`, `apps/api/tests/test_live_sse.py`

**Interfaces:**
- Produces:
  - `OpenF1Client.events_since(session_key: int, after: datetime | None) -> list[LiveEvent]` which fetches `/position`, `/laps`, `/intervals`, `/stints`, `/pit`, `/race_control`, `/weather` and normalises to `LiveEvent` with a monotonically increasing `seq` (assigned by the poller from Redis `INCR live:{key}:seq`).
  - `poll_live_session(ctx, session_key: int)`: poll every 2 s while the `RaceSession.status == "live"`; append each event to Redis stream `live:{session_key}` (`XADD ... MAXLEN ~ 20000`) with fields `seq`, `payload` (JSON); update `live:{session_key}:state` (the reduced `TimingState` as JSON) and set `status` in the stream. If OpenF1 errors, publish `status: waiting`.
  - `GET /v1/live/{session_key}/snapshot` returns the reduced state (ordered tower) as JSON.
  - `GET /v1/live/{session_key}/stream` is `text/event-stream`. Each event has `id: <seq>`, `event: tower`, `data: <TimingState JSON>`. Sends `: heartbeat` comments every 15 s. Resumes from `Last-Event-ID` by replaying stream entries with `seq > id`, then tails. Enforces 3 streams per IP and 500 total (`429` problem otherwise).

- [ ] **Step 1: Write the failing tests**

```python
# apps/api/tests/test_live_sse.py (key tests)
async def test_stream_replays_after_last_event_id(client, redis_seed):
    # redis_seed publishes seq 1..5 into stream live:9999
    async with client.stream("GET", "/v1/live/9999/stream", headers={"Last-Event-ID": "3"}) as r:
        ids = await read_ids(r, count=2)
    assert ids == ["4", "5"]

async def test_stream_sends_heartbeat_when_idle(client, monkeypatch):
    monkeypatch.setattr("f1_api.routers.live.HEARTBEAT_SECONDS", 0.05)
    async with client.stream("GET", "/v1/live/8888/stream") as r:
        first = await read_lines(r, count=1)
    assert first[0].startswith(": heartbeat") or "status" in first[0]

async def test_per_ip_stream_limit_returns_429(client):
    streams = [await open_stream(client) for _ in range(3)]
    r = await client.get("/v1/live/1/stream")
    assert r.status_code == 429
    for s in streams: await s.aclose()

async def test_snapshot_returns_waiting_when_no_data(client):
    r = await client.get("/v1/live/12345/snapshot")
    assert r.status_code == 200 and r.json()["status"] == "waiting"
```

```python
# apps/worker/tests/test_openf1.py
@respx.mock
async def test_normalises_position_and_interval_events() -> None:
    respx.get("https://api.openf1.org/v1/position").mock(return_value=httpx.Response(200, json=[
        {"driver_number": 1, "position": 1, "date": "2025-03-16T04:05:00+00:00"}]))
    respx.get("https://api.openf1.org/v1/intervals").mock(return_value=httpx.Response(200, json=[
        {"driver_number": 4, "gap_to_leader": "+1 LAP", "interval": None, "date": "2025-03-16T04:05:01+00:00"}]))
    # other endpoints empty
    events = await OpenF1Client().events_since(9158, None)
    assert {e.kind for e in events} == {"position", "interval"}
    assert next(e for e in events if e.kind == "interval").data["gap_to_leader"] == "+1 LAP"

@respx.mock
async def test_empty_feed_returns_no_events() -> None: ...

@respx.mock
async def test_http_404_for_unknown_session_returns_empty_and_no_crash() -> None: ...
```

```python
# apps/worker/tests/test_live_poll.py
async def test_poller_publishes_ordered_seq_and_state(redis_url, ...):
    # fake client returns 3 events in two polls; assert stream has seq 1..3 in order
    # and live:{key}:state reflects the reduced state (driver 1 position 1)
async def test_poller_publishes_waiting_status_on_upstream_error(...): ...
async def test_poller_does_not_duplicate_events_across_polls(...): ...
```

Write each test body fully using `fakeredis` is NOT used. Use the Testcontainers `redis_url` fixture from conftest (copy the fixture into `apps/worker/tests/conftest.py`).

- [ ] **Step 2: Run to confirm failure**, then implement

OpenF1 endpoints and normalisation map: `/position` to `position`; `/laps` to `lap` (`lap_duration` seconds to ms, `duration_sector_1..3` to `sectors_ms`, `is_pit_out_lap`); `/intervals` to `interval` (`gap_to_leader`, `interval` verbatim, can be strings or numbers; numbers become `f"+{value:.3f}"`); `/stints` to `stint` (`compound`, `tyre_age_at_start + (lap - lap_start)`); `/pit` to `pit`; `/race_control` to `flag` (when `flag` present); `/weather` to `weather`. Query with `?session_key=<n>&date>=<after ISO>`. A single failed endpoint is logged and skipped. Circuit breaker per client.

The poller reduces events into state with `f1_core.live.reducer.apply_event` and stores JSON with `dataclasses.asdict`. The `seq` is assigned from Redis `INCR`, and the poller remembers `after = max(event.ts)` to avoid duplicates, de-duping on `(kind, driver_number, ts)` via a Redis set with a 10-minute TTL.

SSE route implementation outline (full code required in the file):

```python
HEARTBEAT_SECONDS = 15.0
MAX_PER_IP = 3
MAX_TOTAL = 500


@router.get("/{session_key}/stream")
async def stream(session_key: int, request: Request, redis: RedisDep) -> EventSourceResponse:
    ip = request.client.host if request.client else "unknown"
    if not await _acquire(redis, ip):
        raise ProblemError(429, "Too many streams", "Close another live tab and retry")
    last_id = int(request.headers.get("last-event-id", "0") or 0)

    async def gen() -> AsyncIterator[dict[str, str]]:
        try:
            cursor = "0-0"
            state_key = f"live:{session_key}:state"
            # replay: send current reduced state if the client is behind
            snap = await redis.get(state_key)
            current_seq = json.loads(snap)["last_seq"] if snap else 0
            if snap and current_seq > last_id:
                yield {"id": str(current_seq), "event": "tower", "data": snap}
            last_sent = max(last_id, current_seq)
            while not await request.is_disconnected():
                entries = await redis.xread({f"live:{session_key}": cursor}, block=int(HEARTBEAT_SECONDS * 1000), count=100)
                if not entries:
                    yield {"comment": "heartbeat"}
                    continue
                for _stream, items in entries:
                    for entry_id, fields in items:
                        cursor = entry_id
                        seq = int(fields["seq"])
                        if seq > last_sent:
                            last_sent = seq
                            yield {"id": str(seq), "event": "tower", "data": fields["state"]}
        finally:
            await _release(redis, ip)

    return EventSourceResponse(gen(), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

The poller therefore writes `seq`, `payload` and `state` fields to each stream entry. `_acquire` uses a Redis counter per IP and a global counter with TTL refresh every 30 s so crashed instances do not leak slots.

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest apps/worker apps/api -v`
Expected: all pass. Then `pnpm contract`.

```bash
git add -A && git commit -m "feat(live): openf1 poller, redis stream and sse endpoint with resume"
```

---

### Task 9: Session lifecycle scheduler and live flush

**Files:**
- Create: `apps/worker/src/f1_worker/scheduling.py`, `apps/worker/src/f1_worker/jobs/live_flush.py`
- Modify: `apps/worker/src/f1_worker/settings.py`
- Test: `apps/worker/tests/test_scheduling.py`, `apps/worker/tests/test_live_flush.py`

**Interfaces:**
- Produces:
  - `decide_poll_interval(now, sessions: list[RaceSession]) -> int` returning seconds: `2` while any session is live, `60` within 30 minutes before a start, otherwise `1800`. Pure function, tested exhaustively.
  - `tick_sessions(ctx)` cron (every minute): marks sessions `live` from `starts_at - 5 min` and `finished` from the OpenF1 end signal or `starts_at + 3 h`, enqueues `poll_live_session` for live sessions (unique per session key), resolves `openf1_session_key` by matching OpenF1 `/sessions?year=&session_name=&country_name=`.
  - `flush_live_session(ctx, race_session_id)` at finish: writes `laps`, `pit_stops` and `stints` from OpenF1 into Postgres idempotently, then deletes the Redis stream after a 6 h TTL.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("offset_min,live,expected", [
    (-10, False, 60),       # 10 min before start
    (-40, False, 1800),     # 40 min before start
    (5, True, 2),           # live
    (500, False, 1800),     # long after
])
def test_decide_poll_interval(offset_min, live, expected): ...

def test_cancelled_session_never_goes_live(): ...
async def test_flush_is_idempotent(session_factory): ...
async def test_flush_handles_missing_sector_times_as_none(session_factory): ...
```

- [ ] **Step 2: Implement, wire cron and commit**

`WorkerSettings.cron_jobs` gains: `tick_sessions` every minute, `calendar_task` daily at 03:00 UTC, `constructors_task` and `results_task` hourly (results only for races whose `Race` has a finished `R` session and fewer than expected results), `weather_task` every 3 hours for races within the next 7 days. Each task fetches the current season year from `datetime.now(UTC).year`.

Run: `uv run pytest apps/worker -v`
Expected: pass.

```bash
git add -A && git commit -m "feat(worker): session lifecycle scheduling and live flush"
```

---

### Task 10: Web: app shell, home, calendar, race, driver and team pages

**Files:**
- Create: `apps/web/src/app/{page.tsx,calendar/page.tsx,races/[season]/[round]/page.tsx,drivers/[ref]/page.tsx,teams/[ref]/page.tsx}`, `apps/web/src/components/{app-shell,left-rail,next-race-card,calendar-grid,race-results,driver-header,team-theme}.tsx`, `apps/web/src/lib/format.ts`
- Test: `apps/web/src/lib/format.test.ts`, `apps/web/src/components/{next-race-card,race-results,team-theme}.test.tsx`, `apps/web/e2e/browse.spec.ts`

**Interfaces:**
- Consumes: contract types `RaceSummary`, `RaceDetail`, `DriverProfile`, `TeamProfile`, `ResultRow`.
- Produces:
  - `formatLapTime(ms: number | null): string` (`"1:21.456"`, `"—"` for null), `formatGap(value: string | null): string` (verbatim, `"—"` for null), `formatLocalDateTime(iso: string, locale?: string, timeZone?: string): string`.
  - `<TeamTheme color>` wrapper that sets `--team` on a div for children.
  - `<NextRaceCard race now>` with a countdown that updates each second on the client and shows "Live now" when any session is live.
  - Pages are server components with `fetch` revalidate of 60 s using the typed client with `next: { revalidate: 60 }`.
  - The shell has a left rail on desktop, a bottom nav on mobile, and mounts the command palette fed by `/v1/search` (debounced 150 ms).

- [ ] **Step 1: Write the failing tests**

```ts
// apps/web/src/lib/format.test.ts
import { describe, expect, it } from "vitest";
import { formatGap, formatLapTime, formatLocalDateTime } from "./format";

describe("formatLapTime", () => {
  it("formats minutes, seconds, millis", () => expect(formatLapTime(81456)).toBe("1:21.456"));
  it("pads seconds", () => expect(formatLapTime(60005)).toBe("1:00.005"));
  it("handles sub-minute", () => expect(formatLapTime(59999)).toBe("59.999"));
  it("returns dash for null", () => expect(formatLapTime(null)).toBe("—"));
});
describe("formatGap", () => {
  it("keeps lap gaps verbatim", () => expect(formatGap("+1 LAP")).toBe("+1 LAP"));
  it("dashes null", () => expect(formatGap(null)).toBe("—"));
});
describe("formatLocalDateTime", () => {
  it("converts UTC to the given timezone", () =>
    expect(formatLocalDateTime("2025-03-16T04:00:00Z", "en-GB", "Australia/Melbourne")).toContain("15:00"));
});
```

```tsx
// apps/web/src/components/race-results.test.tsx
it("shows DNF status when position is null", () => { /* row with position null, status 'Retired' renders 'DNF' and 'Retired' */ });
it("shows fractional points", () => { /* 0.5 renders '0.5' */ });
it("renders an empty state when no results", () => { /* 'Results not available yet' */ });
```

```tsx
// apps/web/src/components/team-theme.test.tsx
it("sets the --team css variable", () => {
  const { container } = render(<TeamTheme color="#FF8000"><span>x</span></TeamTheme>);
  expect((container.firstChild as HTMLElement).style.getPropertyValue("--team")).toBe("#FF8000");
});
```

Write the `next-race-card` test with a fake `now` prop to assert "Starts in 2d 3h" and "Live now" states.

- [ ] **Step 2: Run to confirm failure**, then implement

Implement `format.ts`:

```ts
export function formatLapTime(ms: number | null): string {
  if (ms === null) return "—";
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  const millis = ms % 1000;
  const s = String(seconds).padStart(minutes > 0 ? 2 : 1, "0");
  return `${minutes > 0 ? `${minutes}:` : ""}${s}.${String(millis).padStart(3, "0")}`;
}
export const formatGap = (v: string | null) => (v === null || v === "" ? "—" : v);
export function formatLocalDateTime(iso: string, locale = undefined as string | undefined, timeZone?: string) {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short", timeZone, hourCycle: "h23" }).format(new Date(iso));
}
```

Build pages with `getApi()` (no token needed for public endpoints). Driver and team pages wrap content in `<TeamTheme color={profile.color}>`. Race page: tabs for Race, Qualifying, Sprint (hidden if absent), and weather summary. Calendar: a grid grouped by month with a "sprint" badge and local-time session list. Use `generateMetadata` for titles. Add the global command palette host in `layout.tsx` that calls `/v1/search` and navigates with `router.push(hit.href)`.

- [ ] **Step 3: E2E and commit**

`browse.spec.ts` (seeded 2025 data): home shows next race card; `Cmd+K`, type "norris", Enter, lands on `/drivers/norris`; calendar to race page shows results table; driver page accent colour equals team colour (assert computed `--team`).

Run: `pnpm --filter @f1/web test && pnpm --filter @f1/web e2e`
Expected: pass.

```bash
git add -A && git commit -m "feat(web): home, calendar, race, driver, team pages and command palette"
```

---

### Task 11: Web: Live Race Centre

**Files:**
- Create: `apps/web/src/hooks/use-live-session.ts`, `apps/web/src/app/live/[sessionKey]/page.tsx`, `apps/web/src/components/live/{live-tower,flag-banner,stale-banner,weather-panel,live-header}.tsx`
- Test: `apps/web/src/hooks/use-live-session.test.ts`, `apps/web/src/components/live/live-tower.test.tsx`

**Interfaces:**
- Produces: `useLiveSession(sessionKey: number, opts?: { eventSourceFactory?: (url: string) => EventSourceLike; now?: () => number })` returning `{ state: TimingStateDto | null, connection: "connecting" | "live" | "reconnecting" | "stale", lastEventAt: number | null }`. It opens `EventSource` at `${API}/v1/live/${key}/stream`, parses `tower` events, relies on the browser's automatic `Last-Event-ID`, backs off manually (1 s, 2 s, 4 s up to 15 s) after errors that close the source, and marks `stale` when no event or heartbeat arrives for 20 s.
- `<LiveTower rows />` renders `TimingTowerRow`s with FLIP-style reorder animation (translateY transitions, disabled under `prefers-reduced-motion`), `PIT` and `OUT` chips, gap and interval via `formatGap`, tyre compound dot, and sector bar from reducer colours.

- [ ] **Step 1: Write the failing tests**

```ts
// use-live-session.test.ts
it("parses tower events into state", async () => { /* fake EventSource emits tower JSON; hook returns driver order */ });
it("goes stale after 20s of silence", async () => { /* fake timers advance 21s; connection === 'stale' */ });
it("reconnects with backoff after an error", async () => { /* factory called twice; second delayed 1s */ });
it("shows waiting state when server status is waiting", async () => { /* state.status === 'waiting' */ });
it("closes the EventSource on unmount", async () => { /* close called */ });
```

```tsx
// live-tower.test.tsx
it("renders PIT chip for drivers in the pit lane", () => {});
it("renders OUT for retired drivers and sorts them last", () => {});
it("renders verbatim lap gaps like +1 LAP", () => {});
it("shows 'Waiting for live data' instead of an empty tower when waiting", () => {});
```

Write full bodies using `vi.useFakeTimers()`, a hand-rolled `FakeEventSource` class with `emit(type, data, id)` and `close = vi.fn()`, and Testing Library `renderHook` and `act`.

- [ ] **Step 2: Implement and commit**

The page header always shows "Unofficial, community data (OpenF1). Not affiliated with Formula 1." and the freshness line "Updated Xs ago" driven by `lastEventAt`. The stale banner appears when `connection === "stale"`.

Run: `pnpm --filter @f1/web test`
Expected: pass.

```bash
git add -A && git commit -m "feat(web): live race centre with sse hook, tower and stale handling"
```

---

### Task 12: Phase 1 hardening, load check and parity

**Files:**
- Create: `apps/api/tests/load/live_fanout.py` (k6-free async script), `docs/parity/phase-1.md`, `docs/runbooks/live-session.md`
- Test: `apps/web/e2e/live.spec.ts`

- [ ] **Step 1: Replay-driven E2E**

Add a dev-only replay tool `apps/worker/scripts/replay_live.py <fixture.jsonl> --speed 5` that XADDs recorded events into `live:9999` so a full session can be shown without a race. `live.spec.ts` starts the replay, opens `/live/9999`, expects the tower to reorder after a scripted overtake, injects a 25 s gap (pauses replay) and expects the stale banner, then resumes and expects it to clear.

- [ ] **Step 2: Lag and fan-out test**

`live_fanout.py` opens 300 SSE clients with `httpx`, publishes 1 event per second for 60 s with an embedded timestamp, and asserts p95 publish-to-receive latency under 1 s locally (the 5 s budget leaves room for OpenF1 delay). Run: `uv run python apps/api/tests/load/live_fanout.py`. Expected: prints `p95=...ms` under 1000.

- [ ] **Step 3: Parity checklist (legacy features covered)**

`docs/parity/phase-1.md` lists each legacy feature and its new equivalent: live weather (Task 4), championship standings (Phase 0 and Task 3), race weekend forecast (Task 4 and race page), session results (Task 3 and race page), driver and team profiles (Task 5 and 10), dashboard (home). Mark each `done` with the test that proves it. Items for later phases: telemetry, predictions, strategy, favorites, season comparison, pit stop analysis, lap replay.

- [ ] **Step 4: Runbook and commit**

`docs/runbooks/live-session.md`: how to verify the poller during a session, how to restart it, how to replay data, and what users see during an OpenF1 outage.

Run the full suite: `uv run pytest && pnpm test && pnpm --filter @f1/web e2e`
Expected: all green; CI gates pass.

```bash
git add -A && git commit -m "test(live): replay e2e, fan-out check, parity checklist and runbook"
```

Open the PR `phase-1-race-centre` to `main`. Phase 1 exit criterion: during a live session the timing tower updates with under 5 s lag.
