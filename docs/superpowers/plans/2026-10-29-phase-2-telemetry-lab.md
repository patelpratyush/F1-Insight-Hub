# Phase 2: Telemetry Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users compare any two laps from any recent session: speed, throttle, brake, gear traces aligned by distance, a delta-time chart, sector colouring, an interactive track map, pit stop and tyre strategy analysis, and a lap replay.

**Architecture:** A worker job loads sessions with FastF1 once, processes laps and car telemetry into compact Parquet files in object storage (R2 in production, MinIO locally), and records pointers in `telemetry_index`. A pure `f1_core.telemetry` module resamples laps onto a common distance axis and computes deltas and sector colours. The api serves pre-processed slices with long-lived HTTP caching. The web app renders traces with uPlot (canvas) and the track map with SVG.

**Tech Stack:** Phase 0 and 1 stack plus FastF1, pandas, pyarrow, numpy, boto3, uPlot, d3-scale, d3-shape.

**Spec:** `docs/superpowers/specs/2026-10-29-f1-insight-hub-rewrite-design.md`. Depends on: Phases 0 and 1 merged.

## Global Constraints

- Telemetry files are immutable once written (content-addressed key `telemetry/{year}/{round}/{session}/{driver}/{lap}.parquet`). Re-ingestion writes only missing keys.
- Slices are downsampled to at most 500 points per lap on a shared distance axis (metres).
- Telemetry API responses carry `Cache-Control: public, max-age=31536000, immutable` and a strong `ETag` for finished sessions.
- First paint of the compare view under 2.0 s LCP, interaction (cursor move across charts) at 60 fps with two laps.
- FastF1 cache lives on a worker volume (`FASTF1_CACHE_DIR`) and is never committed.
- Telemetry is not available before 2018; the UI states this explicitly.

## Review Focus

1. A driver has no valid lap, or a lap is deleted or is an in/out lap: lap list marks these, compare disables them, nothing crashes. (Task 3, Task 6)
2. Telemetry has gaps, duplicated timestamps or distance that is not monotonic: resampler returns a clean monotonic axis and reports `quality: "degraded"`. (Task 2)
3. Two laps of different length (pit-out lap vs flying lap): the distance axis is normalised to the shorter lap with a flag, and the delta is still defined. (Task 2)
4. Session is in progress or just finished and telemetry is not processed yet: API returns `202` with `processing` status, UI shows a progress state and retries. (Task 5, Task 7)
5. Browser with reduced motion or a small screen: charts stay legible, replay respects reduced motion by defaulting to paused. (Task 8, Task 10)
6. FastF1 or the F1 timing source is unreachable at ingestion: job fails visibly, partial files are not indexed. (Task 1)
7. Same lap requested concurrently by many users: served from cache, no repeated Parquet reads per request. (Task 5)

---

## File Structure

```
packages/db-py/alembic/versions/0004_telemetry.py
packages/db-py/src/f1_db/models/telemetry.py
packages/db-py/src/f1_db/storage.py
packages/core-py/src/f1_core/telemetry/{__init__,resample,delta,sectors,track,quality}.py
packages/core-py/tests/telemetry/test_*.py
apps/worker/src/f1_worker/sources/fastf1_loader.py
apps/worker/src/f1_worker/jobs/telemetry.py
apps/api/src/f1_api/{schemas,services,routers}/telemetry.py
apps/web/src/app/telemetry/page.tsx
apps/web/src/app/telemetry/[season]/[round]/[session]/page.tsx
apps/web/src/components/telemetry/{session-picker,lap-table,trace-chart,delta-chart,track-map,sector-bars,compare-state}.tsx
apps/web/src/app/pit-stops/[season]/[round]/page.tsx
apps/web/src/app/replay/[season]/[round]/page.tsx
```

---

### Task 1: Object storage client and telemetry index

**Files:**
- Create: `packages/db-py/src/f1_db/storage.py`, `packages/db-py/src/f1_db/models/telemetry.py`, `packages/db-py/alembic/versions/0004_telemetry.py`
- Modify: `packages/db-py/src/f1_db/models/__init__.py`
- Test: `packages/db-py/tests/test_storage.py`, `packages/db-py/tests/test_schema_phase2.py`

**Interfaces:**
- Produces:
  - `ObjectStore(endpoint: str | None, access_key: str, secret_key: str, bucket: str)` with `put_bytes(key, data, content_type)`, `get_bytes(key) -> bytes`, `exists(key) -> bool`, `list_prefix(prefix) -> list[str]`. Sync boto3 wrapped by `asyncio.to_thread` in async variants `aput_bytes`, `aget_bytes`, `aexists`.
  - `TelemetryIndex(id, race_session_id, driver_id, lap_number, object_key, points, quality: str, lap_time_ms, created_at)` unique on `(race_session_id, driver_id, lap_number)`.
  - `TelemetryStatus(race_session_id PK/FK, status: "pending"|"processing"|"ready"|"failed", updated_at, error)`.

- [ ] **Step 1: Write the failing tests**

```python
# packages/db-py/tests/test_storage.py  (uses a MinIO testcontainer fixture `store`)
async def test_roundtrip_bytes(store):
    await store.aput_bytes("a/b.parquet", b"123", "application/octet-stream")
    assert await store.aexists("a/b.parquet")
    assert await store.aget_bytes("a/b.parquet") == b"123"

async def test_missing_key_exists_false_and_get_raises_keyerror(store):
    assert not await store.aexists("nope")
    with pytest.raises(KeyError):
        await store.aget_bytes("nope")

async def test_put_is_idempotent_for_same_key(store): ...
```

Fixture `store` in `packages/db-py/tests/conftest.py` uses `testcontainers.minio.MinioContainer`, creates the bucket with boto3, and yields an `ObjectStore`.

- [ ] **Step 2: Run to confirm failure**, then implement

```python
# packages/db-py/src/f1_db/storage.py
import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class ObjectStore:
    def __init__(self, endpoint: str | None, access_key: str, secret_key: str, bucket: str) -> None:
        self.bucket = bucket
        self._s3 = boto3.client(
            "s3", endpoint_url=endpoint, aws_access_key_id=access_key,
            aws_secret_access_key=secret_key, region_name="auto",
            config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
        )

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self._s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def get_bytes(self, key: str) -> bytes:
        try:
            return bytes(self._s3.get_object(Bucket=self.bucket, Key=key)["Body"].read())
        except ClientError as exc:
            if exc.response["Error"]["Code"] in {"NoSuchKey", "404"}:
                raise KeyError(key) from exc
            raise

    def exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    async def aput_bytes(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(self.put_bytes, key, data, content_type)

    async def aget_bytes(self, key: str) -> bytes:
        return await asyncio.to_thread(self.get_bytes, key)

    async def aexists(self, key: str) -> bool:
        return await asyncio.to_thread(self.exists, key)
```

Models and migration follow the Phase 0 pattern (autogenerate with `--rev-id 0004`; migration `0003` is the search migration from Phase 1). Schema test asserts both tables exist and the unique constraint rejects duplicates.

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest packages/db-py -v` (Expected: pass.)

```bash
git add -A && git commit -m "feat(db): add object store client and telemetry index tables"
```

---

### Task 2: Telemetry resampling, delta and quality (pure core)

**Files:**
- Create: `packages/core-py/src/f1_core/telemetry/{__init__,resample,delta,quality}.py`
- Test: `packages/core-py/tests/telemetry/{test_resample.py,test_delta.py,test_quality.py}`

**Interfaces:**
- Produces:
  - `RawLap`: dataclass with numpy arrays `t_s`, `speed_kph`, `throttle_pct`, `brake: bool array`, `gear`, `rpm`, `x`, `y` and `lap_time_ms: int | None`.
  - `ResampledLap`: same channels on `distance_m` axis plus `quality: Literal["good","degraded"]`.
  - `resample_lap(raw: RawLap, n_points: int = 500) -> ResampledLap`: integrates speed over time to get distance, drops non-monotonic and duplicate timestamps, interpolates every channel onto `np.linspace(0, total_distance, n_points)`, forward-fills `gear`, thresholds `brake`, marks `degraded` if more than 5% of samples were dropped or any gap exceeds 1 s.
  - `align_pair(a: ResampledLap, b: ResampledLap) -> tuple[ResampledLap, ResampledLap, bool]`: crops both to the shorter total distance and returns `truncated` flag.
  - `delta_time(a: ResampledLap, b: ResampledLap) -> np.ndarray` giving `time_b(d) - time_a(d)` in seconds at each distance point (positive means `a` is ahead).

- [ ] **Step 1: Write the failing tests**

```python
# packages/core-py/tests/telemetry/test_resample.py
import numpy as np
import pytest
from f1_core.telemetry.resample import RawLap, resample_lap

def make_raw(n=200, speed=200.0, with_dup=False) -> RawLap:
    t = np.linspace(0, 80, n)
    if with_dup:
        t[50] = t[49]
    return RawLap(t_s=t, speed_kph=np.full(n, speed), throttle_pct=np.full(n, 100.0),
                  brake=np.zeros(n, dtype=bool), gear=np.full(n, 7), rpm=np.full(n, 11000.0),
                  x=np.linspace(0, 1000, n), y=np.zeros(n), lap_time_ms=80000)

def test_constant_speed_distance_matches_integral():
    out = resample_lap(make_raw())
    expected = 200.0 / 3.6 * 80
    assert out.distance_m[-1] == pytest.approx(expected, rel=0.01)
    assert len(out.distance_m) == 500
    assert out.quality == "good"

def test_distance_axis_is_strictly_monotonic_even_with_duplicate_timestamps():
    out = resample_lap(make_raw(with_dup=True))
    assert np.all(np.diff(out.distance_m) > 0)

def test_large_time_gap_marks_degraded():
    raw = make_raw()
    raw.t_s[100:] += 5.0
    assert resample_lap(raw).quality == "degraded"

def test_empty_lap_raises_value_error():
    with pytest.raises(ValueError):
        resample_lap(make_raw(n=1))

def test_brake_channel_stays_boolean():
    raw = make_raw(); raw.brake[20:40] = True
    assert resample_lap(raw).brake.dtype == bool
```

```python
# test_delta.py
def test_equal_laps_have_zero_delta(): ...
def test_faster_a_gives_positive_delta_growing_along_lap():
    # a at 220 km/h, b at 200 km/h; delta at end ~ time_b - time_a > 0 and monotonic increasing
def test_align_pair_truncates_to_shorter_and_flags(): ...
def test_delta_is_finite_for_degraded_input(): ...
```

- [ ] **Step 2: Run to confirm failure**, then implement

```python
# packages/core-py/src/f1_core/telemetry/resample.py
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

F = NDArray[np.float64]


@dataclass
class RawLap:
    t_s: F
    speed_kph: F
    throttle_pct: F
    brake: NDArray[np.bool_]
    gear: NDArray[np.int64]
    rpm: F
    x: F
    y: F
    lap_time_ms: int | None


@dataclass
class ResampledLap:
    distance_m: F
    time_s: F
    speed_kph: F
    throttle_pct: F
    brake: NDArray[np.bool_]
    gear: NDArray[np.int64]
    rpm: F
    x: F
    y: F
    lap_time_ms: int | None
    quality: Literal["good", "degraded"]


def resample_lap(raw: RawLap, n_points: int = 500) -> ResampledLap:
    if len(raw.t_s) < 2:
        raise ValueError("lap needs at least two samples")
    order = np.argsort(raw.t_s, kind="stable")
    keep = np.concatenate(([True], np.diff(raw.t_s[order]) > 0))
    idx = order[keep]
    dropped = 1 - len(idx) / len(raw.t_s)
    t = raw.t_s[idx]
    v_ms = raw.speed_kph[idx] / 3.6
    dist = np.concatenate(([0.0], np.cumsum(0.5 * (v_ms[1:] + v_ms[:-1]) * np.diff(t))))
    strictly = np.concatenate(([True], np.diff(dist) > 1e-9))
    t, dist = t[strictly], dist[strictly]
    idx = idx[strictly]
    if len(dist) < 2:
        raise ValueError("lap has no distance travelled")
    grid = np.linspace(0, dist[-1], n_points)

    def lerp(ch: F) -> F:
        return np.interp(grid, dist, ch[idx])

    gear_idx = np.searchsorted(dist, grid, side="right").clip(1, len(dist)) - 1
    gap = float(np.max(np.diff(t))) > 1.0
    quality: Literal["good", "degraded"] = "degraded" if dropped > 0.05 or gap else "good"
    return ResampledLap(
        distance_m=grid, time_s=np.interp(grid, dist, t - t[0]), speed_kph=lerp(raw.speed_kph),
        throttle_pct=lerp(raw.throttle_pct), brake=lerp(raw.brake.astype(float)) >= 0.5,
        gear=raw.gear[idx][gear_idx], rpm=lerp(raw.rpm), x=lerp(raw.x), y=lerp(raw.y),
        lap_time_ms=raw.lap_time_ms, quality=quality,
    )
```

```python
# packages/core-py/src/f1_core/telemetry/delta.py
import numpy as np
from f1_core.telemetry.resample import F, ResampledLap


def align_pair(a: ResampledLap, b: ResampledLap) -> tuple[ResampledLap, ResampledLap, bool]:
    limit = min(a.distance_m[-1], b.distance_m[-1])
    truncated = not np.isclose(a.distance_m[-1], b.distance_m[-1], rtol=0.005)
    return _crop(a, limit), _crop(b, limit), bool(truncated)


def _crop(lap: ResampledLap, limit: float) -> ResampledLap:
    mask = lap.distance_m <= limit + 1e-9
    fields = {k: (v[mask] if hasattr(v, "__len__") and getattr(v, "ndim", 0) else v)
              for k, v in lap.__dict__.items()}
    return ResampledLap(**fields)


def delta_time(a: ResampledLap, b: ResampledLap) -> F:
    grid = np.linspace(0, min(a.distance_m[-1], b.distance_m[-1]), min(len(a.distance_m), len(b.distance_m)))
    ta = np.interp(grid, a.distance_m, a.time_s)
    tb = np.interp(grid, b.distance_m, b.time_s)
    return tb - ta
```

Complete `quality.py` with `summarize_quality(laps) -> Literal["good","degraded"]` (worst of inputs) and tests.

- [ ] **Step 3: Run to confirm pass (90% coverage) and commit**

Run: `uv run pytest packages/core-py --cov=f1_core --cov-fail-under=90`
Expected: pass.

```bash
git add -A && git commit -m "feat(core): telemetry resampling, alignment and delta time"
```

---

### Task 3: Sector colouring and lap validity (pure core)

**Files:**
- Create: `packages/core-py/src/f1_core/telemetry/sectors.py`
- Test: `packages/core-py/tests/telemetry/test_sectors.py`

**Interfaces:**
- Produces:
  - `LapSummary(driver_ref, lap_number, lap_time_ms, s1_ms, s2_ms, s3_ms, is_pit_in, is_pit_out, deleted: bool, compound)`.
  - `is_valid_lap(l: LapSummary) -> bool` (has a time, not deleted, not an in or out lap).
  - `color_sectors(laps: list[LapSummary]) -> dict[tuple[str,int], tuple[SectorColor, SectorColor, SectorColor]]` keyed by `(driver_ref, lap_number)` using purple (overall best among valid laps), green (driver's personal best so far), yellow (otherwise), `none` for missing.

- [ ] **Step 1: Write the failing tests**

```python
def test_invalid_laps_are_excluded_from_bests(): ...
def test_overall_best_sector_is_purple_and_personal_green(): ...
def test_missing_sector_is_none_not_yellow(): ...
def test_in_and_out_laps_are_invalid(): ...
def test_driver_with_no_valid_laps_returns_all_none(): ...
```

- [ ] **Step 2: Implement and commit**

Process laps in `(lap_number)` order so "personal best so far" is chronological; compute overall best across valid laps only; invalid laps still get colours relative to existing bests but never set them.

Run: `uv run pytest packages/core-py/tests/telemetry/test_sectors.py -v` (Expected: pass.)

```bash
git add -A && git commit -m "feat(core): sector colouring and lap validity rules"
```

---

### Task 4: FastF1 processing job

**Files:**
- Create: `apps/worker/src/f1_worker/sources/fastf1_loader.py`, `apps/worker/src/f1_worker/jobs/telemetry.py`
- Modify: `apps/worker/src/f1_worker/settings.py`, `apps/worker/pyproject.toml` (add `fastf1`, `pandas`, `pyarrow`, `numpy`)
- Test: `apps/worker/tests/test_telemetry_job.py`, fixtures `apps/worker/tests/fixtures/fastf1_session.pkl`

**Interfaces:**
- Produces:
  - `SessionData` protocol: `laps() -> list[LapSummary]` and `lap_telemetry(driver_ref, lap_number) -> RawLap | None`. `FastF1Loader.load(year, round, session_type) -> SessionData` (the only code that imports `fastf1`). Tests use a `FakeSessionData`.
  - `process_session_telemetry(session_factory, store, loader, race_session_id) -> int`: sets `TelemetryStatus` to `processing`, for each valid lap with telemetry resamples, serialises to Parquet (columns `distance_m,time_s,speed_kph,throttle_pct,brake,gear,rpm,x,y`, zstd), writes to `telemetry/{year}/{round}/{type}/{driver_ref}/{lap}.parquet` only if missing, upserts `TelemetryIndex` and `LapRecord` rows, finally sets `ready`. On any exception sets `failed`, stores the error, and does not index partial files. Returns count of laps indexed.

- [ ] **Step 1: Write the failing tests** using a `FakeSessionData` built from `make_raw()` helpers

```python
async def test_processes_valid_laps_and_skips_invalid(...):
    # 3 laps: valid, pit-out, deleted. Expect 1 index row, 1 object in store, status ready.
async def test_rerun_does_not_rewrite_existing_objects(...):
    # put_count on a spy store stays at 1 after two runs
async def test_loader_failure_sets_failed_and_indexes_nothing(...): ...
async def test_missing_telemetry_for_a_lap_is_skipped_not_fatal(...): ...
async def test_status_is_processing_during_run(...): ...
```

- [ ] **Step 2: Implement and commit**

FastF1 specifics inside `fastf1_loader.py`: `fastf1.Cache.enable_cache(os.environ["FASTF1_CACHE_DIR"])`, `session = fastf1.get_session(year, round, type_name)`, `session.load(laps=True, telemetry=True, weather=False, messages=False)`. Map our types to FastF1 names (`R: "R"`, `Q: "Q"`, `SPRINT: "S"`, `SQ: "SQ"`, `FP1..3: "FP1".."FP3"`). Use `lap.get_car_data().add_distance()` and `get_pos_data()` merged by time (`merge_channels`), convert `Brake` bool, `Throttle`, `nGear`, `RPM`, `Speed`, `X`, `Y`. `deleted` from `lap["Deleted"]`. Run FastF1 inside `asyncio.to_thread` because it is blocking. Years before 2018 raise `UnsupportedSessionError` which maps to status `failed` with message "Telemetry unavailable before 2018".

Add Arq task `telemetry_task(ctx, race_session_id)`; enqueue from `tick_sessions` when a session becomes `finished`, and from a daily backfill cron that walks the last 3 finished sessions with `TelemetryStatus` missing or `failed`.

Run: `uv run pytest apps/worker/tests/test_telemetry_job.py -v` (Expected: pass.)

```bash
git add -A && git commit -m "feat(worker): process fastf1 sessions into parquet telemetry"
```

---

### Task 5: Telemetry API

**Files:**
- Create: `apps/api/src/f1_api/{schemas,services,routers}/telemetry.py`
- Modify: `apps/api/src/f1_api/main.py`, `apps/api/src/f1_api/config.py` (S3 settings), `apps/api/src/f1_api/deps.py` (`StoreDep`)
- Test: `apps/api/tests/test_telemetry_api.py`

**Interfaces:**
- Produces (all under `/v1/telemetry`):
  - `GET /sessions?season=` returns sessions with `telemetry_status`.
  - `GET /{season}/{round}/{session}/laps` returns `list[LapOut]`: `{driver, lap_number, lap_time_ms, sectors_ms: [..], sector_colors: [..], valid: bool, compound, pit_in, pit_out}` and `status`. Returns `202` with `{"status": "processing"}` and `Retry-After: 15` when not ready.
  - `GET /{season}/{round}/{session}/compare?a=<driver>:<lap>&b=<driver>:<lap>` returns `{distance_m: [...], a: {...channels}, b: {...channels}, delta_s: [...], truncated: bool, quality: "good"|"degraded"}`. `422` if `a` or `b` is malformed or refers to an invalid lap. `404` if the lap has no telemetry.
  - `GET /{season}/{round}/{session}/track?driver=&lap=` returns `{x: [...], y: [...], corners?: [...]}` for the map.
- Caching: finished sessions get `Cache-Control: public, max-age=31536000, immutable` and a strong ETag (`sha256` of the body); in-process LRU (256 entries) caches decoded Parquet by key so concurrent requests reuse it.

- [ ] **Step 1: Write the failing tests**

```python
async def test_laps_202_while_processing(client, seeded_processing): 
    r = await client.get("/v1/telemetry/2031/1/R/laps")
    assert r.status_code == 202 and r.headers["retry-after"] == "15"

async def test_compare_returns_aligned_channels_and_delta(client, seeded_ready):
    r = await client.get("/v1/telemetry/2031/1/R/compare", params={"a": "nor:12", "b": "ver:12"})
    body = r.json()
    assert len(body["distance_m"]) == len(body["a"]["speed_kph"]) == len(body["delta_s"])
    assert r.headers["cache-control"].endswith("immutable")

@pytest.mark.parametrize("a", ["nor", "nor:x", ":3", "nor:3:4", "nor:-1"])
async def test_malformed_lap_ref_is_422(client, seeded_ready, a): ...

async def test_invalid_lap_is_422(client, seeded_ready):
    # pit-out lap
async def test_missing_telemetry_is_404_problem(client, seeded_ready): ...
async def test_laps_endpoint_marks_invalid_laps(client, seeded_ready): ...
async def test_parquet_decoded_once_for_concurrent_requests(client, seeded_ready, spy_store):
    await asyncio.gather(*[client.get(url) for _ in range(10)])
    assert spy_store.get_count == 2   # one per lap
```

`seeded_ready` writes real Parquet fixtures into a MinIO testcontainer via `ObjectStore` and inserts `TelemetryIndex`/`LapRecord` rows.

- [ ] **Step 2: Implement and commit**

Parse `a`/`b` with a strict regex `^([a-z0-9_]{2,40}):([1-9][0-9]{0,2})$`. Read Parquet with `pyarrow.parquet.read_table(io.BytesIO(bytes))`, convert to `ResampledLap`, run `align_pair` and `delta_time`, round floats to 3 decimals before serialising to keep payloads small. Use `functools.lru_cache`-style async cache keyed by object key (a small `AsyncLRU` helper in `f1_api/cache.py` that stores futures so concurrent callers share one load).

Run: `uv run pytest apps/api -v && pnpm contract`
Expected: pass.

```bash
git add -A && git commit -m "feat(api): add telemetry laps, compare and track endpoints"
```

---

### Task 6: Web: session picker and lap selection

**Files:**
- Create: `apps/web/src/app/telemetry/page.tsx`, `apps/web/src/app/telemetry/[season]/[round]/[session]/page.tsx`, `apps/web/src/components/telemetry/{session-picker,lap-table,compare-state}.tsx`, `apps/web/src/lib/compare-url.ts`
- Test: `apps/web/src/lib/compare-url.test.ts`, `apps/web/src/components/telemetry/lap-table.test.tsx`

**Interfaces:**
- Produces: `parseCompare(search: URLSearchParams) -> { a: LapRef | null; b: LapRef | null }`, `buildCompare(a, b) -> string` (query `a=nor:12&b=ver:12`); selection state lives in the URL so links are shareable. `<LapTable laps selected onSelect />` shows lap time, sector colour pills, compound dot; invalid laps are greyed with a reason tooltip and cannot be selected; fastest valid lap per driver has a "Best" badge.

- [ ] **Step 1: Write the failing tests** (`parseCompare` rejects malformed refs, round-trips; `LapTable` disables invalid laps, marks best lap, supports keyboard selection with Enter and Space)

- [ ] **Step 2: Implement and commit**

Server page fetches `/laps`; when the response status is 202 it renders `<ProcessingState />` that polls every 10 s with `router.refresh()` and shows elapsed time.

Run: `pnpm --filter @f1/web test` (Expected: pass.)

```bash
git add -A && git commit -m "feat(web): telemetry session picker and lap selection"
```

---

### Task 7: Web: trace charts, delta chart and sector bars

**Files:**
- Create: `apps/web/src/components/telemetry/{trace-chart,delta-chart,sector-bars}.tsx`, `apps/web/src/lib/uplot-sync.ts`
- Test: `apps/web/src/components/telemetry/{trace-chart,sector-bars}.test.tsx`, `apps/web/e2e/telemetry.spec.ts`

**Interfaces:**
- Produces: `<TraceChart channel="speed_kph" | "throttle_pct" | "brake" | "gear" | "rpm" data syncKey colors />` using uPlot, with a shared cursor across charts via `uPlot.sync(syncKey)`, drivers in their team colours (second driver of the same team gets a dashed line), axis in metres, and a legend showing hovered values with tabular numerals. `<DeltaChart delta distance />` fills area above and below zero in each driver's colour. `<SectorBars a b />` shows three bars per driver in purple, green or yellow with the sector time. Respects `prefers-reduced-motion` (no animated transitions) and exposes an accessible data table fallback behind a "View as table" toggle.

- [ ] **Step 1: Write the failing tests** (component renders a canvas and a `figure` with an accessible name; the data-table toggle lists values; same-team colour handling; empty data renders an explanatory empty state, not a blank chart)

- [ ] **Step 2: Implement, then E2E**

`telemetry.spec.ts` runs against seeded data: choose two laps, charts render (`canvas` count is at least 4), hovering one chart moves the cursor on the others (assert via exposed `data-cursor-index` attribute), the delta chart sign matches the faster lap, and the page meets the LCP budget via `page.evaluate` on `PerformanceObserver`.

Run: `pnpm --filter @f1/web test && pnpm --filter @f1/web e2e` (Expected: pass.)

```bash
git add -A && git commit -m "feat(web): synchronized telemetry traces, delta chart and sector bars"
```

---

### Task 8: Web: interactive track map

**Files:**
- Create: `apps/web/src/components/telemetry/track-map.tsx`, `apps/web/src/lib/track-geometry.ts`
- Test: `apps/web/src/lib/track-geometry.test.ts`, `apps/web/src/components/telemetry/track-map.test.tsx`

**Interfaces:**
- Produces: `normalizeTrack(x: number[], y: number[], size: number, padding: number) -> { points: [number, number][]; path: string }` (fits into a square preserving aspect ratio, flips Y), `<TrackMap x y colorBy="speed" | "delta" | "driver" cursorIndex />` drawing an SVG path coloured per segment, with a car marker at `cursorIndex` driven by the same cursor as the charts, and the start/finish line. The line draws itself on first render (stroke-dashoffset animation) unless reduced motion.

- [ ] **Step 1: Write the failing tests** (normalise preserves aspect ratio; empty and single-point input return an empty path; degenerate zero-width track does not divide by zero; marker position matches `cursorIndex`)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(web): interactive track map with cursor-synced marker"
```

---

### Task 9: Pit stop and tyre strategy analysis

**Files:**
- Create: `apps/api/src/f1_api/{schemas,services,routers}/strategy_history.py`, `apps/web/src/app/pit-stops/[season]/[round]/page.tsx`, `apps/web/src/components/telemetry/{stint-timeline,pit-table}.tsx`
- Test: `apps/api/tests/test_pit_stops_api.py`, `apps/web/src/components/telemetry/stint-timeline.test.tsx`

**Interfaces:**
- Produces: `GET /v1/races/{season}/{round}/strategy` returning `{drivers: [{driver, stints: [{n, compound, lap_start, lap_end, laps}], pit_stops: [{lap, duration_ms}]}], total_laps}` from `stints` and `pit_stops` tables (populated in Phase 1 Task 9 flush). `<StintTimeline />` draws horizontal bars per driver coloured by compound (soft red, medium yellow, hard white, intermediate green, wet blue) with pit markers; the pit table sorts by duration and highlights fastest stop.

- [ ] **Step 1: Write the failing tests** (driver with zero stops; stint with `lap_end = null` extends to total laps; fastest stop highlighted; unknown compound renders neutral grey; wet races with intermediate-to-slick changes)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat: pit stop and tyre stint analysis"
```

---

### Task 10: Lap replay

**Files:**
- Create: `apps/web/src/app/replay/[season]/[round]/page.tsx`, `apps/web/src/components/telemetry/replay-player.tsx`, `apps/web/src/hooks/use-replay-clock.ts`
- Test: `apps/web/src/hooks/use-replay-clock.test.ts`, `apps/web/e2e/replay.spec.ts`

**Interfaces:**
- Produces: `useReplayClock({ durationMs, speed, startPaused })` returning `{ t, playing, play, pause, seek, setSpeed }` driven by `requestAnimationFrame`, clamped to `[0, durationMs]`, exposes `speed` options `0.25, 0.5, 1, 2, 4`. `<ReplayPlayer />` plays two laps simultaneously on the track map by time (using `time_s` from each lap), shows live gap, and defaults to paused when `prefers-reduced-motion` is set. Keyboard: Space toggles, arrows seek 1 s.

- [ ] **Step 1: Write the failing tests** (clock advances with fake rAF; clamps at end and stops; seek clamps below 0; speed change preserves position; unmount cancels rAF)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(web): two-lap replay with synchronized clock"
```

---

### Task 11: Phase 2 hardening and parity

**Files:**
- Create: `docs/parity/phase-2.md`, `docs/runbooks/telemetry.md`, `apps/worker/scripts/backfill_telemetry.py`
- Test: `apps/api/tests/load/telemetry_compare.py`

- [ ] **Step 1: Performance check**

`telemetry_compare.py` fires 200 concurrent compare requests for the same lap pair and 200 for distinct pairs; assert p95 under 300 ms (cache hit path under 50 ms) and that Parquet reads per unique lap equal 1. Run: `uv run python apps/api/tests/load/telemetry_compare.py`. Expected: prints p95 values within budget.

- [ ] **Step 2: Backfill and runbook**

`backfill_telemetry.py --season 2025 --rounds 1-24` enqueues `telemetry_task` for every finished session with a progress bar and safe resume. The runbook explains cache directory sizing, how to reprocess one session (`--force` deletes index rows, not objects), and what to do if FastF1 changes its schema.

- [ ] **Step 3: Parity and commit**

`docs/parity/phase-2.md` maps legacy features to new ones: session telemetry (Tasks 4 to 7), speed trace with throttle and brake overlay (Task 7), driver comparison (Task 5 and 7), track map (Task 8), sector analysis (Task 3 and 7), lap replay (Task 10), pit stop analysis (Task 9).

Run: `uv run pytest && pnpm test && pnpm --filter @f1/web e2e`
Expected: green.

```bash
git add -A && git commit -m "test(telemetry): load check, backfill tool, runbook and parity"
```

Open the PR `phase-2-telemetry-lab`. Exit criterion: two drivers' laps compare smoothly within the performance budget.
