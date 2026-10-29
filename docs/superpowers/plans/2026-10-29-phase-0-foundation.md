# Phase 0: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the new monorepo, design system, API, worker, database, auth, observability and CI/CD, proven by one vertical slice: a signed-in user views `/standings` served from Postgres through the typed client, fed by a scheduled Jolpica ingestion job.

**Architecture:** pnpm + Turborepo for TypeScript (`apps/web`, `packages/ui`, `packages/contract`), a uv workspace for Python (`apps/api`, `apps/worker`, `packages/core-py`, `packages/db-py`). The api and worker share models through `f1_db`. The api never calls upstream sources. The contract is generated from the FastAPI OpenAPI spec.

**Tech Stack:** Node 22, pnpm 9, Turborepo, Next.js 16 (App Router), React 19, Tailwind v4, Radix, cmdk, Storybook, Vitest, Playwright, Better Auth, Python 3.12, uv, FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, Arq, httpx, tenacity, PyJWT, OpenTelemetry, Sentry, Postgres 16, Redis 7, MinIO, Terraform, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-29-f1-insight-hub-rewrite-design.md` (sections 3 to 7). Amendments are in `2026-10-29-00-index.md`.

## Global Constraints

- Node `>=22`, pnpm `9.12.0`, Python `>=3.12`, Postgres 16, Redis 7.
- TypeScript `strict: true`. Python `mypy --strict` and `ruff` must pass.
- UUIDv7 primary keys and `timestamptz` for every timestamp.
- Every endpoint is under `/v1`. Errors use RFC 9457 `application/problem+json` and include `request_id`.
- Api never calls upstream data sources during a user request.
- Ingested rows carry `source` and `ingested_at` and are written with idempotent upserts.
- Domain core (`f1_core`) performs no I/O.
- No code is copied from the legacy codebase.
- SLOs to design for: p95 cached read under 200 ms, LCP under 2.0 s.
- Dark theme by default, tokens defined once in `packages/ui`.

## Review Focus

1. Jolpica returns an empty `StandingsLists` (pre-season or no data): ingestion writes nothing and succeeds, and `GET /v1/standings/drivers` returns `200` with `[]`. (Task 9, Task 12)
2. Jolpica returns 429 or 5xx repeatedly: retries back off, the circuit opens, the job records `failed`, and the api keeps serving the last good data with its freshness timestamp. (Task 12)
3. The `season` query parameter is `abc`, `1900` or `3000`: respond `422` problem+json, never a 500. (Task 7)
4. Two ingestion runs execute concurrently for the same season: no duplicate rows, and the final state is correct. (Task 12)
5. Redis is down: rate limiting fails open with a logged warning, `/readyz` returns `503`, and `/healthz` still returns `200`. (Task 6)
6. Points are fractional (for example `0.5`, `12.5`): stored and returned exactly, not rounded to an integer. (Task 4, Task 7)
7. An unauthenticated user opens `/standings`: redirected to `/sign-in?next=/standings`, and returned there after signing in. (Task 14)

---

## File Structure

```
.github/workflows/ci.yml, deploy.yml
.gitignore  .editorconfig  .pre-commit-config.yaml  .env.example
package.json  pnpm-workspace.yaml  turbo.json  tsconfig.base.json
pyproject.toml  uv.lock  Makefile  docker-compose.yml
docs/adr/0001-monorepo.md  0002-job-queue-arq.md  0003-auth-better-auth.md
apps/api/pyproject.toml
apps/api/src/f1_api/{__init__,main,config,errors,deps,telemetry,logging_setup}.py
apps/api/src/f1_api/middleware/{request_id.py,rate_limit.py}
apps/api/src/f1_api/auth/jwt.py
apps/api/src/f1_api/routers/{health.py,standings.py,meta.py}
apps/api/src/f1_api/schemas/{standings.py,meta.py}
apps/api/src/f1_api/services/standings.py
apps/api/scripts/export_openapi.py
apps/api/tests/{conftest.py,test_*.py}
apps/worker/pyproject.toml
apps/worker/src/f1_worker/{__init__,settings,resilience,runs}.py
apps/worker/src/f1_worker/sources/jolpica.py
apps/worker/src/f1_worker/jobs/standings.py
apps/worker/tests/{conftest.py,fixtures/driver_standings_2025.json,test_*.py}
packages/core-py/pyproject.toml  src/f1_core/{__init__,ids}.py  tests/test_ids.py
packages/db-py/pyproject.toml  alembic.ini  alembic/{env.py,versions/}
packages/db-py/src/f1_db/{__init__,base,session}.py  models/*.py
packages/db-py/tests/{conftest.py,test_schema.py}
packages/contract/{package.json,openapi.json,src/index.ts,src/schema.d.ts}
packages/ui/{package.json,src/**,.storybook/*}
apps/web/{package.json,next.config.ts,src/**,e2e/**}
infra/terraform/{main.tf,variables.tf,outputs.tf}  infra/fly/{api.fly.toml,worker.fly.toml}
infra/docker/{api.Dockerfile,worker.Dockerfile}
```

---

### Task 1: Archive legacy and scaffold the monorepo

**Files:**
- Create: `package.json`, `pnpm-workspace.yaml`, `turbo.json`, `tsconfig.base.json`, `.gitignore`, `.editorconfig`, `.pre-commit-config.yaml`, `docs/adr/0001-monorepo.md`
- Delete: everything tracked outside `docs/`

**Interfaces:**
- Produces: root scripts `pnpm build|lint|typecheck|test` (all via Turborepo) that later tasks hook into.

- [ ] **Step 1: Preserve the old code on a branch**

```bash
git checkout main
git branch legacy main
git push origin legacy   # if a remote exists
git checkout -b phase-0-foundation
```

Expected: `git branch` lists `legacy` and `phase-0-foundation`.

- [ ] **Step 2: Remove all old tracked code except `docs/`**

```bash
git ls-files | grep -v '^docs/' | xargs git rm -q
rm -rf node_modules dist backend src public .venv
ls -A
```

Expected: only `.git` and `docs` remain (plus untracked local files you do not care about).

- [ ] **Step 3: Write `package.json`**

```json
{
  "name": "f1-insight-hub",
  "private": true,
  "packageManager": "pnpm@9.12.0",
  "engines": { "node": ">=22" },
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev --parallel",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "test": "turbo run test",
    "contract": "turbo run generate --filter=@f1/contract"
  },
  "devDependencies": {
    "turbo": "^2.3.0",
    "typescript": "^5.6.0"
  }
}
```

- [ ] **Step 4: Write `pnpm-workspace.yaml`, `turbo.json`, `tsconfig.base.json`**

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": [".next/**", "dist/**", "storybook-static/**"] },
    "generate": { "outputs": ["src/schema.d.ts"] },
    "dev": { "cache": false, "persistent": true },
    "lint": { "dependsOn": ["^build"] },
    "typecheck": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["^build"] }
  }
}
```

```json
// tsconfig.base.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "resolveJsonModule": true,
    "jsx": "preserve"
  }
}
```

- [ ] **Step 5: Write `.gitignore`, `.editorconfig`, `.pre-commit-config.yaml`**

```gitignore
node_modules
.next
dist
storybook-static
.turbo
coverage
.venv
__pycache__
.mypy_cache
.ruff_cache
.pytest_cache
.env
.env.local
*.tsbuildinfo
playwright-report
test-results
.terraform
*.tfstate*
```

```ini
# .editorconfig
root = true
[*]
indent_style = space
indent_size = 2
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
[*.py]
indent_size = 4
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: local
    hooks:
      - id: prettier
        name: prettier
        entry: pnpm exec prettier --write
        language: system
        types_or: [ts, tsx, json, css, md]
```

- [ ] **Step 6: Write ADR 0001**

```markdown
# ADR 0001: Monorepo with pnpm/Turborepo and a uv workspace

Status: Accepted (2026-10-29)

## Context
Web (TypeScript) and data services (Python) must share one typed contract and ship together.

## Decision
One repository. Turborepo orchestrates TypeScript packages. A uv workspace orchestrates Python packages. The OpenAPI spec exported by the api is the single source of the TS client.

## Consequences
CI must cache both toolchains. Contributors need Node 22 and uv installed.
```

- [ ] **Step 7: Install and verify**

Run: `pnpm install && pnpm exec turbo run build --dry`
Expected: exits 0 with "No tasks" or an empty task graph.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: archive legacy and scaffold new monorepo"
```

---

### Task 2: Python workspace and `f1_core` (UUIDv7)

**Files:**
- Create: `pyproject.toml`, `packages/core-py/pyproject.toml`, `packages/core-py/src/f1_core/__init__.py`, `packages/core-py/src/f1_core/ids.py`
- Test: `packages/core-py/tests/test_ids.py`

**Interfaces:**
- Produces: `f1_core.ids.uuid7() -> uuid.UUID` (time-ordered, version 7), used as the default primary key factory in `f1_db`.

- [ ] **Step 1: Write root `pyproject.toml`**

```toml
[project]
name = "f1-insight-hub"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv.workspace]
members = ["apps/api", "apps/worker", "packages/core-py", "packages/db-py"]

[tool.uv.sources]
f1-core = { workspace = true }
f1-db = { workspace = true }

[dependency-groups]
dev = [
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
  "pytest-cov>=5.0",
  "hypothesis>=6.115",
  "mypy>=1.13",
  "ruff>=0.8",
  "httpx>=0.27",
  "respx>=0.21",
  "testcontainers[postgres,redis]>=4.8",
  "asgi-lifespan>=2.1",
]

[tool.ruff]
line-length = 100
target-version = "py312"
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "ASYNC", "S", "SIM", "RUF"]
ignore = ["S101"]

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
```

- [ ] **Step 2: Write `packages/core-py/pyproject.toml`**

```toml
[project]
name = "f1-core"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/f1_core"]
```

`packages/core-py/src/f1_core/__init__.py` is an empty file.

- [ ] **Step 3: Write the failing test**

```python
# packages/core-py/tests/test_ids.py
import time
import uuid

from f1_core.ids import uuid7


def test_uuid7_has_version_7_and_rfc_variant() -> None:
    value = uuid7()
    assert isinstance(value, uuid.UUID)
    assert value.version == 7
    assert value.variant == uuid.RFC_4122


def test_uuid7_is_time_ordered() -> None:
    first = uuid7()
    time.sleep(0.005)
    second = uuid7()
    assert first.int < second.int


def test_uuid7_is_unique_across_many_calls() -> None:
    assert len({uuid7() for _ in range(10_000)}) == 10_000
```

- [ ] **Step 4: Run it to confirm failure**

Run: `uv sync --all-packages && uv run pytest packages/core-py/tests/test_ids.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'f1_core.ids'`.

- [ ] **Step 5: Implement**

```python
# packages/core-py/src/f1_core/ids.py
import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Return a time-ordered UUIDv7 (48-bit ms timestamp, 74 random bits)."""
    millis = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10), "big")
    rand_a = (rand >> 62) & 0xFFF
    rand_b = rand & ((1 << 62) - 1)
    value = (
        ((millis & ((1 << 48) - 1)) << 80)
        | (0x7 << 76)
        | (rand_a << 64)
        | (0b10 << 62)
        | rand_b
    )
    return uuid.UUID(int=value)
```

- [ ] **Step 6: Run to confirm pass**

Run: `uv run pytest packages/core-py/tests/test_ids.py -v`
Expected: 3 passed.

- [ ] **Step 7: Lint, type check, commit**

```bash
uv run ruff check packages/core-py && uv run mypy packages/core-py/src
git add -A && git commit -m "feat(core): add uuid7 generator and python workspace"
```

---

### Task 3: Local infrastructure (Docker Compose)

**Files:**
- Create: `docker-compose.yml`, `.env.example`, `Makefile`

**Interfaces:**
- Produces: Postgres on `localhost:5432` (db `f1`, user `f1`, password `f1`), Redis on `6379`, MinIO on `9000` (console `9001`, user `minio`, password `minio12345`, bucket `f1-telemetry`).

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: f1
      POSTGRES_USER: f1
      POSTGRES_PASSWORD: f1
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U f1 -d f1"]
      interval: 5s
      timeout: 3s
      retries: 10
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio12345
    ports: ["9000:9000", "9001:9001"]
    volumes: ["miniodata:/data"]
  minio-init:
    image: minio/mc:latest
    depends_on: [minio]
    entrypoint: >
      /bin/sh -c "sleep 3 &&
      mc alias set local http://minio:9000 minio minio12345 &&
      mc mb --ignore-existing local/f1-telemetry"
volumes:
  pgdata:
  miniodata:
```

- [ ] **Step 2: Write `.env.example`**

```bash
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://f1:f1@localhost:5432/f1
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio12345
S3_BUCKET=f1-telemetry
AUTH_ISSUER=http://localhost:3000
AUTH_JWKS_URL=http://localhost:3000/api/auth/jwks
CORS_ORIGINS=http://localhost:3000
BETTER_AUTH_SECRET=dev-only-secret-change-me-32-chars-min
BETTER_AUTH_URL=http://localhost:3000
AUTH_DATABASE_URL=postgresql://f1:f1@localhost:5432/f1?options=-c%20search_path%3Dauth
API_BASE_URL=http://localhost:8000
SENTRY_DSN=
OTEL_EXPORTER_OTLP_ENDPOINT=
```

- [ ] **Step 3: Write `Makefile`**

```make
.PHONY: up down migrate api worker web test
up:
	docker compose up -d --wait postgres redis minio minio-init
down:
	docker compose down
migrate:
	uv run --directory packages/db-py alembic upgrade head
api:
	uv run uvicorn f1_api.main:app --reload --port 8000
worker:
	uv run arq f1_worker.settings.WorkerSettings
web:
	pnpm --filter @f1/web dev
test:
	uv run pytest && pnpm test
```

- [ ] **Step 4: Verify**

Run: `cp .env.example .env && make up && docker compose ps`
Expected: `postgres` and `redis` show `healthy`, `minio` running.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore(infra): add docker compose for postgres, redis, minio"
```

---

### Task 4: Database package, models and baseline migration

**Files:**
- Create: `packages/db-py/pyproject.toml`, `alembic.ini`, `alembic/env.py`, `src/f1_db/{__init__,base,session}.py`, `src/f1_db/models/{__init__,reference,standings,results,ops}.py`
- Test: `packages/db-py/tests/{conftest.py,test_schema.py}`

**Interfaces:**
- Consumes: `f1_core.ids.uuid7`.
- Produces:
  - `f1_db.base.Base`, `f1_db.base.utcnow() -> datetime`
  - `f1_db.session.make_engine(url: str) -> AsyncEngine`, `make_session_factory(engine) -> async_sessionmaker[AsyncSession]`
  - Models: `Season(id, year)`, `Team(id, ref, name, nationality)`, `Driver(id, ref, code, given_name, family_name, number, nationality)`, `Race(id, season_id, round, name, circuit_name, race_date)`, `DriverStanding(id, season_id, round, driver_id, team_id, position, points: Decimal, wins, source, ingested_at)`, `SessionResult(...)`, `IngestionRun(id, job, started_at, finished_at, status, rows, error)`.

- [ ] **Step 1: Write `packages/db-py/pyproject.toml`**

```toml
[project]
name = "f1-db"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
  "f1-core",
  "sqlalchemy[asyncio]>=2.0.36",
  "asyncpg>=0.30",
  "alembic>=1.14",
  "boto3>=1.35",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/f1_db"]
```

- [ ] **Step 2: Write `base.py` and `session.py`**

```python
# packages/db-py/src/f1_db/base.py
import uuid
from datetime import UTC, datetime

from f1_core.ids import uuid7
from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)


class IngestedMixin:
    source: Mapped[str] = mapped_column(default="unknown")
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
```

```python
# packages/db-py/src/f1_db/session.py
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def make_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=10)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
```

`src/f1_db/__init__.py` is empty.

- [ ] **Step 3: Write models**

```python
# packages/db-py/src/f1_db/models/reference.py
import uuid
from datetime import date

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class Season(IdMixin, Base):
    __tablename__ = "seasons"
    year: Mapped[int] = mapped_column(unique=True)


class Team(IdMixin, IngestedMixin, Base):
    __tablename__ = "teams"
    ref: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    nationality: Mapped[str | None]


class Driver(IdMixin, IngestedMixin, Base):
    __tablename__ = "drivers"
    ref: Mapped[str] = mapped_column(unique=True)
    code: Mapped[str | None]
    given_name: Mapped[str]
    family_name: Mapped[str]
    number: Mapped[int | None]
    nationality: Mapped[str | None]


class Race(IdMixin, IngestedMixin, Base):
    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("season_id", "round"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    round: Mapped[int]
    name: Mapped[str]
    circuit_name: Mapped[str]
    race_date: Mapped[date]
```

```python
# packages/db-py/src/f1_db/models/standings.py
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class DriverStanding(IdMixin, IngestedMixin, Base):
    __tablename__ = "driver_standings"
    __table_args__ = (UniqueConstraint("season_id", "round", "driver_id"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"), index=True)
    round: Mapped[int]
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int]
    points: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    wins: Mapped[int]
```

```python
# packages/db-py/src/f1_db/models/results.py
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class SessionResult(IdMixin, IngestedMixin, Base):
    __tablename__ = "session_results"
    __table_args__ = (UniqueConstraint("race_id", "session_type", "driver_id"),)
    race_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("races.id"), index=True)
    session_type: Mapped[str]
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int | None]
    grid: Mapped[int | None]
    status: Mapped[str | None]
    points: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    time_ms: Mapped[int | None]
```

```python
# packages/db-py/src/f1_db/models/ops.py
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, utcnow


class IngestionRun(IdMixin, Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (Index("ix_ingestion_runs_job_started", "job", "started_at"),)
    job: Mapped[str]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str]  # running | success | failed
    rows: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None]


_ = uuid  # keep import used for type checkers on some versions
```

```python
# packages/db-py/src/f1_db/models/__init__.py
from f1_db.models.ops import IngestionRun
from f1_db.models.reference import Driver, Race, Season, Team
from f1_db.models.results import SessionResult
from f1_db.models.standings import DriverStanding

__all__ = [
    "Driver", "DriverStanding", "IngestionRun", "Race", "Season", "SessionResult", "Team",
]
```

- [ ] **Step 4: Write Alembic config**

```ini
# packages/db-py/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = src
[loggers]
keys = root
[handlers]
keys = console
[formatters]
keys = generic
[logger_root]
level = WARN
handlers = console
[handler_console]
class = StreamHandler
args = (sys.stderr,)
formatter = generic
[formatter_generic]
format = %(levelname)s %(name)s %(message)s
```

```python
# packages/db-py/alembic/env.py
import asyncio
import os

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import f1_db.models  # noqa: F401  (register models)
from f1_db.base import Base

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    return os.environ["DATABASE_URL"]


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _do_run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _url()
    engine = async_engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_do_run)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

Create an empty `packages/db-py/alembic/versions/.gitkeep`.

- [ ] **Step 5: Write the failing schema test and fixtures**

```python
# packages/db-py/tests/conftest.py
import os
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.postgres import PostgresContainer

from f1_db.session import make_engine

DB_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        url = pg.get_connection_url()
        env = {**os.environ, "DATABASE_URL": url}
        subprocess.run(["alembic", "upgrade", "head"], cwd=DB_DIR, env=env, check=True)
        yield url


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    eng = make_engine(database_url)
    yield eng
    await eng.dispose()
```

```python
# packages/db-py/tests/test_schema.py
from decimal import Decimal

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from f1_db.models import Driver, DriverStanding, Season, Team
from f1_db.session import make_session_factory

EXPECTED = {
    "seasons", "teams", "drivers", "races", "driver_standings",
    "session_results", "ingestion_runs", "alembic_version",
}


async def test_baseline_creates_expected_tables(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert EXPECTED <= names


async def test_auth_schema_exists(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        row = await conn.execute(
            text("select 1 from information_schema.schemata where schema_name = 'auth'")
        )
    assert row.scalar() == 1


async def test_fractional_points_round_trip(engine: AsyncEngine) -> None:
    factory = make_session_factory(engine)
    async with factory() as s:
        season = Season(year=2099)
        team = Team(ref="t-frac", name="T", nationality=None)
        driver = Driver(ref="d-frac", code="FRC", given_name="A", family_name="B")
        s.add_all([season, team, driver])
        await s.flush()
        s.add(
            DriverStanding(
                season_id=season.id, round=1, driver_id=driver.id, team_id=team.id,
                position=1, points=Decimal("12.50"), wins=0,
            )
        )
        await s.commit()
        got = (await s.execute(text("select points from driver_standings"))).scalar_one()
    assert got == Decimal("12.50")
```

- [ ] **Step 6: Run to confirm failure**

Run: `uv sync --all-packages && uv run pytest packages/db-py/tests -v`
Expected: FAIL because the migration has no versions (tables missing).

- [ ] **Step 7: Generate the baseline migration**

```bash
export DATABASE_URL=postgresql+asyncpg://f1:f1@localhost:5432/f1
uv run --directory packages/db-py alembic revision --autogenerate -m "baseline" --rev-id 0001
```

Open `packages/db-py/alembic/versions/0001_baseline.py`. At the top of `upgrade()` add `op.execute("CREATE SCHEMA IF NOT EXISTS auth")`, and at the bottom of `downgrade()` add `op.execute("DROP SCHEMA IF EXISTS auth CASCADE")`. Confirm it creates all seven tables.

- [ ] **Step 8: Run to confirm pass**

Run: `uv run pytest packages/db-py/tests -v`
Expected: 3 passed.

- [ ] **Step 9: Commit**

```bash
uv run ruff check packages/db-py && uv run mypy packages/db-py/src
git add -A && git commit -m "feat(db): add models, baseline migration and auth schema"
```

---

### Task 5: API skeleton: config, errors, request IDs, health

**Files:**
- Create: `apps/api/pyproject.toml`, `src/f1_api/{__init__,config,errors,deps,main}.py`, `src/f1_api/middleware/{__init__,request_id}.py`, `src/f1_api/routers/{__init__,health}.py`
- Test: `apps/api/tests/{conftest.py,test_errors.py,test_health.py}`

**Interfaces:**
- Produces:
  - `f1_api.config.Settings` (fields: `environment`, `database_url`, `redis_url`, `auth_issuer`, `auth_jwks_url`, `cors_origins: list[str]`, `sentry_dsn`, `otlp_endpoint`) and `get_settings()`.
  - `f1_api.errors.ProblemError(status: int, title: str, detail: str | None = None, type_: str = "about:blank")`.
  - `f1_api.main.create_app(settings: Settings | None = None) -> FastAPI`.
  - Header `X-Request-ID` on every response; problem bodies include `request_id`.
  - Routes `GET /healthz` (liveness, always 200) and `GET /readyz` (200 only if Postgres and Redis respond, otherwise 503).

- [ ] **Step 1: Write `apps/api/pyproject.toml`**

```toml
[project]
name = "f1-api"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
  "f1-core", "f1-db",
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "pydantic>=2.9",
  "pydantic-settings>=2.6",
  "redis>=5.2",
  "pyjwt[crypto]>=2.10",
  "httpx>=0.27",
  "structlog>=24.4",
  "sentry-sdk[fastapi]>=2.19",
  "opentelemetry-sdk>=1.28",
  "opentelemetry-exporter-otlp>=1.28",
  "opentelemetry-instrumentation-fastapi>=0.49b0",
  "opentelemetry-instrumentation-sqlalchemy>=0.49b0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/f1_api"]
```

- [ ] **Step 2: Write the failing tests**

```python
# apps/api/tests/conftest.py
from collections.abc import AsyncIterator, Iterator
import os
import subprocess
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from f1_api.config import Settings
from f1_api.main import create_app

DB_DIR = Path(__file__).resolve().parents[3] / "packages" / "db-py"


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        url = pg.get_connection_url()
        subprocess.run(
            ["alembic", "upgrade", "head"], cwd=DB_DIR, check=True,
            env={**os.environ, "DATABASE_URL": url},
        )
        yield url


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    with RedisContainer("redis:7-alpine") as r:
        yield f"redis://{r.get_container_host_ip()}:{r.get_exposed_port(6379)}/0"


@pytest.fixture
def settings(pg_url: str, redis_url: str) -> Settings:
    return Settings(
        environment="test", database_url=pg_url, redis_url=redis_url,
        auth_issuer="http://auth.test", auth_jwks_url="http://auth.test/jwks",
        cors_origins=["http://localhost:3000"],
    )


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
```

```python
# apps/api/tests/test_errors.py
from httpx import AsyncClient


async def test_unknown_route_returns_problem_json_with_request_id(client: AsyncClient) -> None:
    resp = await client.get("/v1/nope", headers={"X-Request-ID": "req-123"})
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.headers["x-request-id"] == "req-123"
    body = resp.json()
    assert body["status"] == 404
    assert body["request_id"] == "req-123"


async def test_request_id_generated_when_absent(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert len(resp.headers["x-request-id"]) >= 16
```

```python
# apps/api/tests/test_health.py
from httpx import AsyncClient


async def test_healthz_is_ok(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_readyz_ok_when_dependencies_up(client: AsyncClient) -> None:
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["postgres"] == "ok"
    assert resp.json()["redis"] == "ok"
```

- [ ] **Step 3: Run to confirm failure**

Run: `uv sync --all-packages && uv run pytest apps/api/tests -v`
Expected: FAIL with `ModuleNotFoundError: f1_api.config`.

- [ ] **Step 4: Implement config, errors, middleware**

```python
# apps/api/src/f1_api/config.py
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://f1:f1@localhost:5432/f1"
    redis_url: str = "redis://localhost:6379/0"
    auth_issuer: str = "http://localhost:3000"
    auth_jwks_url: str = "http://localhost:3000/api/auth/jwks"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    sentry_dsn: str = ""
    otlp_endpoint: str = Field(default="", validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```python
# apps/api/src/f1_api/errors.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM = "application/problem+json"


class ProblemError(Exception):
    def __init__(
        self, status: int, title: str, detail: str | None = None, type_: str = "about:blank"
    ) -> None:
        self.status, self.title, self.detail, self.type_ = status, title, detail, type_


def _problem(request: Request, status: int, title: str, detail: str | None,
             type_: str = "about:blank", extra: dict[str, object] | None = None) -> JSONResponse:
    body: dict[str, object] = {
        "type": type_, "title": title, "status": status,
        "detail": detail, "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", None),
    }
    if extra:
        body.update(extra)
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem_error(request: Request, exc: ProblemError) -> JSONResponse:
        return _problem(request, exc.status, exc.title, exc.detail, exc.type_)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(request, exc.status_code, str(exc.detail), None)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        return _problem(request, 422, "Validation error", "Request validation failed",
                        extra={"errors": errors})

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        return _problem(request, 500, "Internal server error", None)
```

```python
# apps/api/src/f1_api/middleware/request_id.py
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        rid = headers.get(b"x-request-id", b"").decode() or uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = rid

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = [*message.get("headers", []), (b"x-request-id", rid.encode())]
            await send(message)

        await self.app(scope, receive, send_with_id)
```

- [ ] **Step 5: Implement deps, health router, `create_app`**

```python
# apps/api/src/f1_api/deps.py
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


DbSession = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]
```

```python
# apps/api/src/f1_api/routers/health.py
from fastapi import APIRouter, Response
from sqlalchemy import text

from f1_api.deps import DbSession, RedisDep

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(db: DbSession, redis: RedisDep, response: Response) -> dict[str, str]:
    result = {"postgres": "ok", "redis": "ok"}
    try:
        await db.execute(text("select 1"))
    except Exception:
        result["postgres"] = "down"
    try:
        await redis.ping()
    except Exception:
        result["redis"] = "down"
    if "down" in result.values():
        response.status_code = 503
    return result
```

```python
# apps/api/src/f1_api/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from f1_api.config import Settings, get_settings
from f1_api.errors import install_error_handlers
from f1_api.middleware.request_id import RequestIdMiddleware
from f1_api.routers import health
from f1_db.session import make_engine, make_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(cfg.database_url)
        app.state.engine = engine
        app.state.session_factory = make_session_factory(engine)
        app.state.redis = Redis.from_url(cfg.redis_url, decode_responses=True)
        app.state.settings = cfg
        try:
            yield
        finally:
            await app.state.redis.aclose()
            await engine.dispose()

    app = FastAPI(title="F1 Insight Hub API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=cfg.cors_origins, allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    install_error_handlers(app)
    app.include_router(health.router)
    return app
```

There is no module-level `app`. Run uvicorn with the factory flag: `uvicorn f1_api.main:create_app --factory`. Update the `Makefile` `api` target in this step to `uv run uvicorn f1_api.main:create_app --factory --reload --port 8000`.

- [ ] **Step 6: Run to confirm pass**

Run: `uv run pytest apps/api/tests -v`
Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
uv run ruff check apps/api && uv run mypy apps/api/src
git add -A && git commit -m "feat(api): add app factory, problem+json errors, request ids, health"
```

---

### Task 6: Redis rate limiting (fails open)

**Files:**
- Create: `apps/api/src/f1_api/middleware/rate_limit.py`
- Modify: `apps/api/src/f1_api/main.py` (nothing global; the limiter is a dependency)
- Test: `apps/api/tests/test_rate_limit.py`

**Interfaces:**
- Produces: `rate_limit(limit: int, window_seconds: int) -> Callable` returning a FastAPI dependency. Over the limit raises `ProblemError(429, "Too many requests")` and sets `Retry-After`. If Redis errors, the request is allowed and a warning is logged.

- [ ] **Step 1: Write the failing tests**

```python
# apps/api/tests/test_rate_limit.py
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from f1_api.errors import install_error_handlers
from f1_api.middleware.rate_limit import rate_limit


def _app(redis: Redis) -> FastAPI:
    app = FastAPI()
    app.state.redis = redis
    install_error_handlers(app)

    @app.get("/limited", dependencies=[Depends(rate_limit(3, 60))])
    async def limited() -> dict[str, str]:
        return {"ok": "yes"}

    return app


async def test_blocks_after_limit(redis_url: str) -> None:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    async with AsyncClient(transport=ASGITransport(app=_app(redis)), base_url="http://t") as c:
        codes = [(await c.get("/limited")).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    await redis.aclose()


async def test_retry_after_header_present(redis_url: str) -> None:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    async with AsyncClient(transport=ASGITransport(app=_app(redis)), base_url="http://t") as c:
        for _ in range(3):
            await c.get("/limited")
        resp = await c.get("/limited")
    assert resp.status_code == 429
    assert int(resp.headers["retry-after"]) > 0
    await redis.aclose()


async def test_fails_open_when_redis_down() -> None:
    dead = Redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=0.2)
    async with AsyncClient(transport=ASGITransport(app=_app(dead)), base_url="http://t") as c:
        resp = await c.get("/limited")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest apps/api/tests/test_rate_limit.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

```python
# apps/api/src/f1_api/middleware/rate_limit.py
import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request

from f1_api.errors import ProblemError

log = logging.getLogger(__name__)


def rate_limit(limit: int, window_seconds: int) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        bucket = int(time.time()) // window_seconds
        key = f"rl:{request.url.path}:{client}:{bucket}"
        try:
            redis = request.app.state.redis
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window_seconds)
        except Exception:
            log.warning("rate limiter unavailable, failing open")
            return
        if count > limit:
            retry_after = window_seconds - (int(time.time()) % window_seconds)
            err = ProblemError(429, "Too many requests", f"Retry in {retry_after}s")
            err.headers = {"Retry-After": str(retry_after)}  # type: ignore[attr-defined]
            raise err

    return dependency
```

Update `ProblemError` handler in `errors.py` to forward headers: in `_problem_error`, build the response, then `getattr(exc, "headers", None)` and set `resp.headers.update(...)`. Replace the handler body with:

```python
    @app.exception_handler(ProblemError)
    async def _problem_error(request: Request, exc: ProblemError) -> JSONResponse:
        resp = _problem(request, exc.status, exc.title, exc.detail, exc.type_)
        for k, v in getattr(exc, "headers", {}).items():
            resp.headers[k] = v
        return resp
```

Also add `headers: dict[str, str]` as an instance attribute in `ProblemError.__init__` (`self.headers: dict[str, str] = {}`) and remove the `type: ignore` in the limiter.

- [ ] **Step 4: Run to confirm pass**

Run: `uv run pytest apps/api/tests/test_rate_limit.py -v`
Expected: 3 passed.

- [ ] **Step 5: Add the readiness-down test for Redis and commit**

```python
# append to apps/api/tests/test_health.py
from redis.asyncio import Redis


async def test_readyz_503_when_redis_down(client: AsyncClient) -> None:
    client._transport.app.state.redis = Redis.from_url(  # type: ignore[attr-defined]
        "redis://127.0.0.1:1/0", socket_connect_timeout=0.2
    )
    resp = await client.get("/readyz")
    assert resp.status_code == 503
    assert resp.json()["redis"] == "down"
    assert (await client.get("/healthz")).status_code == 200
```

Run: `uv run pytest apps/api/tests -v`
Expected: all pass.

```bash
git add -A && git commit -m "feat(api): add fail-open redis rate limiting"
```

---

### Task 7: Standings endpoint

**Files:**
- Create: `apps/api/src/f1_api/schemas/{__init__,standings}.py`, `src/f1_api/services/{__init__,standings}.py`, `src/f1_api/routers/standings.py`
- Modify: `apps/api/src/f1_api/main.py` (include router)
- Test: `apps/api/tests/test_standings.py`

**Interfaces:**
- Consumes: `f1_db.models`, `DbSession`, `rate_limit`.
- Produces: `GET /v1/standings/drivers?season=<int, default current year>` returning `list[DriverStandingOut]` where `DriverStandingOut = {position: int, points: Decimal(as string-safe number), wins: int, driver: {id, code, given_name, family_name, number}, team: {id, name}, season: int, round: int, updated_at: datetime}`. Valid `season` range: 1950 to current year + 1.
- Service: `StandingsService(session).latest_driver_standings(year: int) -> list[DriverStandingOut]`.

- [ ] **Step 1: Write the failing tests**

```python
# apps/api/tests/test_standings.py
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from f1_db.models import Driver, DriverStanding, Season, Team
from f1_db.session import make_engine, make_session_factory


@pytest.fixture
async def seeded(pg_url: str) -> None:
    engine = make_engine(pg_url)
    async with make_session_factory(engine)() as s:
        await s.execute(text("truncate driver_standings, drivers, teams, seasons cascade"))
        season = Season(year=2031)
        team = Team(ref="mcl", name="McLaren", nationality="British")
        d1 = Driver(ref="nor", code="NOR", given_name="Lando", family_name="Norris", number=4)
        d2 = Driver(ref="pia", code="PIA", given_name="Oscar", family_name="Piastri", number=81)
        s.add_all([season, team, d1, d2])
        await s.flush()
        for rnd, pts_n, pts_p in [(1, "25", "18"), (2, "37.50", "43")]:
            s.add_all([
                DriverStanding(season_id=season.id, round=int(rnd), driver_id=d1.id,
                               team_id=team.id, position=1 if rnd == 1 else 2,
                               points=Decimal(pts_n), wins=1),
                DriverStanding(season_id=season.id, round=int(rnd), driver_id=d2.id,
                               team_id=team.id, position=2 if rnd == 1 else 1,
                               points=Decimal(pts_p), wins=0),
            ])
        await s.commit()
    await engine.dispose()


async def test_returns_latest_round_ordered_by_position(client: AsyncClient, seeded: None) -> None:
    resp = await client.get("/v1/standings/drivers", params={"season": 2031})
    assert resp.status_code == 200
    rows = resp.json()
    assert [r["driver"]["code"] for r in rows] == ["PIA", "NOR"]
    assert all(r["round"] == 2 for r in rows)


async def test_fractional_points_preserved(client: AsyncClient, seeded: None) -> None:
    rows = (await client.get("/v1/standings/drivers", params={"season": 2031})).json()
    nor = next(r for r in rows if r["driver"]["code"] == "NOR")
    assert nor["points"] == 37.5


async def test_empty_season_returns_empty_list(client: AsyncClient) -> None:
    resp = await client.get("/v1/standings/drivers", params={"season": 2030})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize("bad", ["abc", "1900", "3000", "-1"])
async def test_invalid_season_is_422_problem(client: AsyncClient, bad: str) -> None:
    resp = await client.get("/v1/standings/drivers", params={"season": bad})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest apps/api/tests/test_standings.py -v`
Expected: FAIL (404 route not found).

- [ ] **Step 3: Implement schema, service, router**

```python
# apps/api/src/f1_api/schemas/standings.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class DriverRef(BaseModel):
    id: uuid.UUID
    code: str | None
    given_name: str
    family_name: str
    number: int | None


class TeamRef(BaseModel):
    id: uuid.UUID
    name: str


class DriverStandingOut(BaseModel):
    position: int
    points: float
    wins: int
    driver: DriverRef
    team: TeamRef
    season: int
    round: int
    updated_at: datetime
```

```python
# apps/api/src/f1_api/services/standings.py
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.schemas.standings import DriverRef, DriverStandingOut, TeamRef
from f1_db.models import Driver, DriverStanding, Season, Team


class StandingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def latest_driver_standings(self, year: int) -> list[DriverStandingOut]:
        latest_round = (
            select(func.max(DriverStanding.round))
            .join(Season, Season.id == DriverStanding.season_id)
            .where(Season.year == year)
            .scalar_subquery()
        )
        stmt = (
            select(DriverStanding, Driver, Team)
            .join(Season, Season.id == DriverStanding.season_id)
            .join(Driver, Driver.id == DriverStanding.driver_id)
            .join(Team, Team.id == DriverStanding.team_id)
            .where(Season.year == year, DriverStanding.round == latest_round)
            .order_by(DriverStanding.position)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            DriverStandingOut(
                position=s.position, points=float(s.points), wins=s.wins,
                driver=DriverRef(id=d.id, code=d.code, given_name=d.given_name,
                                 family_name=d.family_name, number=d.number),
                team=TeamRef(id=t.id, name=t.name),
                season=year, round=s.round, updated_at=s.ingested_at,
            )
            for s, d, t in rows
        ]
```

```python
# apps/api/src/f1_api/routers/standings.py
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from f1_api.deps import DbSession
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.standings import DriverStandingOut
from f1_api.services.standings import StandingsService

router = APIRouter(prefix="/v1/standings", tags=["standings"])


def _max_year() -> int:
    return datetime.now(UTC).year + 1


@router.get(
    "/drivers", response_model=list[DriverStandingOut],
    dependencies=[Depends(rate_limit(120, 60))], operation_id="getDriverStandings",
)
async def driver_standings(
    db: DbSession,
    season: Annotated[int | None, Query(ge=1950, le=2100)] = None,
) -> list[DriverStandingOut]:
    year = season if season is not None else datetime.now(UTC).year
    if year > _max_year():
        from f1_api.errors import ProblemError

        raise ProblemError(422, "Validation error", "season is in the far future")
    return await StandingsService(db).latest_driver_standings(year)
```

In `main.py` add `from f1_api.routers import health, standings` and `app.include_router(standings.router)`. Note `ge=1950, le=2100` makes `3000` a 422 via validation, and the extra check handles 2102 to 2100 gaps; keep both.

- [ ] **Step 4: Run to confirm pass**

Run: `uv run pytest apps/api/tests/test_standings.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff check apps/api && uv run mypy apps/api/src
git add -A && git commit -m "feat(api): add GET /v1/standings/drivers"
```

---

### Task 8: Freshness endpoint

**Files:**
- Create: `apps/api/src/f1_api/schemas/meta.py`, `routers/meta.py`
- Modify: `apps/api/src/f1_api/main.py`
- Test: `apps/api/tests/test_meta.py`

**Interfaces:**
- Produces: `GET /v1/meta/freshness` returning `list[FreshnessOut]` where `FreshnessOut = {job: str, last_success_at: datetime | None, last_status: str}`. One entry per distinct `ingestion_runs.job`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_meta.py
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import text

from f1_db.models import IngestionRun
from f1_db.session import make_engine, make_session_factory


async def test_freshness_reports_last_success_per_job(client: AsyncClient, pg_url: str) -> None:
    engine = make_engine(pg_url)
    now = datetime.now(UTC)
    async with make_session_factory(engine)() as s:
        await s.execute(text("truncate ingestion_runs"))
        s.add_all([
            IngestionRun(job="standings", started_at=now - timedelta(hours=2),
                         finished_at=now - timedelta(hours=2), status="success", rows=20),
            IngestionRun(job="standings", started_at=now, finished_at=now,
                         status="failed", rows=0, error="boom"),
        ])
        await s.commit()
    await engine.dispose()

    rows = (await client.get("/v1/meta/freshness")).json()
    entry = next(r for r in rows if r["job"] == "standings")
    assert entry["last_status"] == "failed"
    assert entry["last_success_at"] is not None
```

- [ ] **Step 2: Run to confirm failure**, then implement

Run: `uv run pytest apps/api/tests/test_meta.py -v` (Expected: FAIL 404.)

```python
# apps/api/src/f1_api/schemas/meta.py
from datetime import datetime

from pydantic import BaseModel


class FreshnessOut(BaseModel):
    job: str
    last_success_at: datetime | None
    last_status: str
```

```python
# apps/api/src/f1_api/routers/meta.py
from fastapi import APIRouter
from sqlalchemy import func, select

from f1_api.deps import DbSession
from f1_api.schemas.meta import FreshnessOut
from f1_db.models import IngestionRun

router = APIRouter(prefix="/v1/meta", tags=["meta"])


@router.get("/freshness", response_model=list[FreshnessOut], operation_id="getFreshness")
async def freshness(db: DbSession) -> list[FreshnessOut]:
    jobs = (await db.execute(select(IngestionRun.job).distinct())).scalars().all()
    out: list[FreshnessOut] = []
    for job in jobs:
        last_success = (
            await db.execute(
                select(func.max(IngestionRun.finished_at)).where(
                    IngestionRun.job == job, IngestionRun.status == "success"
                )
            )
        ).scalar()
        last_status = (
            await db.execute(
                select(IngestionRun.status)
                .where(IngestionRun.job == job)
                .order_by(IngestionRun.started_at.desc())
                .limit(1)
            )
        ).scalar_one()
        out.append(FreshnessOut(job=job, last_success_at=last_success, last_status=last_status))
    return out
```

Include the router in `main.py`: `from f1_api.routers import health, meta, standings` and `app.include_router(meta.router)`.

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest apps/api/tests -v`
Expected: all pass.

```bash
git add -A && git commit -m "feat(api): add ingestion freshness endpoint"
```

---

### Task 9: Worker resilience primitives (circuit breaker, runs)

**Files:**
- Create: `apps/worker/pyproject.toml`, `src/f1_worker/{__init__,resilience,runs}.py`
- Test: `apps/worker/tests/{conftest.py,test_resilience.py,test_runs.py}`

**Interfaces:**
- Produces:
  - `CircuitBreaker(failure_threshold: int, reset_seconds: float, clock: Callable[[], float] = time.monotonic)` with `async call(fn: Callable[[], Awaitable[T]]) -> T`, raising `CircuitOpenError` while open. States: closed, open, half-open (one trial call after `reset_seconds`).
  - `record_run(session_factory, job: str) -> AsyncContextManager[RunHandle]`; `RunHandle.rows: int` settable. On exit writes `IngestionRun` with status `success` or `failed` (error text), re-raising exceptions.

- [ ] **Step 1: Write `apps/worker/pyproject.toml`**

```toml
[project]
name = "f1-worker"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
  "f1-core", "f1-db",
  "arq>=0.26",
  "httpx>=0.27",
  "tenacity>=9.0",
  "structlog>=24.4",
  "pydantic-settings>=2.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/f1_worker"]
```

- [ ] **Step 2: Write the failing tests**

```python
# apps/worker/tests/test_resilience.py
import pytest

from f1_worker.resilience import CircuitBreaker, CircuitOpenError


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


async def _fail() -> None:
    raise RuntimeError("upstream down")


async def _ok() -> str:
    return "ok"


async def test_opens_after_threshold_and_blocks_calls() -> None:
    cb = CircuitBreaker(failure_threshold=2, reset_seconds=30, clock=Clock())
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(_fail)
    with pytest.raises(CircuitOpenError):
        await cb.call(_ok)


async def test_half_open_trial_closes_on_success() -> None:
    clock = Clock()
    cb = CircuitBreaker(failure_threshold=1, reset_seconds=30, clock=clock)
    with pytest.raises(RuntimeError):
        await cb.call(_fail)
    clock.now = 31
    assert await cb.call(_ok) == "ok"
    assert await cb.call(_ok) == "ok"


async def test_half_open_trial_failure_reopens() -> None:
    clock = Clock()
    cb = CircuitBreaker(failure_threshold=1, reset_seconds=30, clock=clock)
    with pytest.raises(RuntimeError):
        await cb.call(_fail)
    clock.now = 31
    with pytest.raises(RuntimeError):
        await cb.call(_fail)
    with pytest.raises(CircuitOpenError):
        await cb.call(_ok)
```

```python
# apps/worker/tests/conftest.py
import os
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer

from f1_db.session import make_engine, make_session_factory

DB_DIR = Path(__file__).resolve().parents[3] / "packages" / "db-py"


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        url = pg.get_connection_url()
        subprocess.run(["alembic", "upgrade", "head"], cwd=DB_DIR, check=True,
                       env={**os.environ, "DATABASE_URL": url})
        yield url


@pytest.fixture
async def session_factory(pg_url: str) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_engine(pg_url)
    yield make_session_factory(engine)
    await engine.dispose()
```

```python
# apps/worker/tests/test_runs.py
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_db.models import IngestionRun
from f1_worker.runs import record_run


async def test_success_run_recorded(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with record_run(session_factory, "t-success") as run:
        run.rows = 7
    async with session_factory() as s:
        row = (await s.execute(select(IngestionRun).where(IngestionRun.job == "t-success"))).scalar_one()
    assert row.status == "success" and row.rows == 7 and row.finished_at is not None


async def test_failed_run_recorded_and_reraised(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(ValueError, match="bad"):
        async with record_run(session_factory, "t-fail"):
            raise ValueError("bad")
    async with session_factory() as s:
        row = (await s.execute(select(IngestionRun).where(IngestionRun.job == "t-fail"))).scalar_one()
    assert row.status == "failed" and "bad" in (row.error or "")
```

- [ ] **Step 3: Run to confirm failure**

Run: `uv sync --all-packages && uv run pytest apps/worker/tests -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 4: Implement**

```python
# apps/worker/src/f1_worker/resilience.py
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is open."""


class CircuitBreaker:
    def __init__(
        self, failure_threshold: int, reset_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self.clock = clock
        self.failures = 0
        self.opened_at: float | None = None

    def _allow(self) -> bool:
        if self.opened_at is None:
            return True
        if self.clock() - self.opened_at >= self.reset_seconds:
            return True  # half-open: allow one trial
        return False

    async def call(self, fn: Callable[[], Awaitable[T]]) -> T:
        if not self._allow():
            raise CircuitOpenError("circuit open")
        try:
            result = await fn()
        except Exception:
            self.failures += 1
            if self.opened_at is not None or self.failures >= self.failure_threshold:
                self.opened_at = self.clock()
            raise
        self.failures = 0
        self.opened_at = None
        return result
```

```python
# apps/worker/src/f1_worker/runs.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_db.base import utcnow
from f1_db.models import IngestionRun


@dataclass
class RunHandle:
    rows: int = 0


@asynccontextmanager
async def record_run(
    session_factory: async_sessionmaker[AsyncSession], job: str
) -> AsyncIterator[RunHandle]:
    handle = RunHandle()
    run = IngestionRun(job=job, status="running")
    async with session_factory() as s:
        s.add(run)
        await s.commit()
        run_id = run.id
    try:
        yield handle
    except Exception as exc:
        async with session_factory() as s:
            row = await s.get(IngestionRun, run_id)
            assert row is not None
            row.status, row.finished_at, row.error = "failed", utcnow(), str(exc)[:2000]
            await s.commit()
        raise
    async with session_factory() as s:
        row = await s.get(IngestionRun, run_id)
        assert row is not None
        row.status, row.finished_at, row.rows = "success", utcnow(), handle.rows
        await s.commit()
```

- [ ] **Step 5: Run to confirm pass and commit**

Run: `uv run pytest apps/worker/tests -v`
Expected: 5 passed.

```bash
git add -A && git commit -m "feat(worker): add circuit breaker and ingestion run recording"
```

---

### Task 10: Jolpica source adapter

**Files:**
- Create: `apps/worker/src/f1_worker/sources/{__init__,jolpica}.py`, `apps/worker/tests/fixtures/driver_standings_2025.json`
- Test: `apps/worker/tests/test_jolpica.py`

**Interfaces:**
- Produces:
  - Dataclasses `ParsedStanding(round: int, position: int, points: Decimal, wins: int, driver_ref: str, driver_code: str | None, given_name: str, family_name: str, number: int | None, driver_nationality: str | None, team_ref: str, team_name: str, team_nationality: str | None)`.
  - `JolpicaClient(base_url: str = "https://api.jolpi.ca/ergast/f1", client: httpx.AsyncClient | None = None, breaker: CircuitBreaker | None = None)` with `async driver_standings(year: int) -> list[ParsedStanding]`. Returns `[]` when `StandingsLists` is empty. Retries on 429 and 5xx (3 attempts, exponential backoff starting 0.5 s, honouring `Retry-After`), then raises `httpx.HTTPStatusError`.

- [ ] **Step 1: Write the recorded fixture**

```json
// apps/worker/tests/fixtures/driver_standings_2025.json
{
  "MRData": {
    "StandingsTable": {
      "season": "2025",
      "StandingsLists": [
        {
          "season": "2025",
          "round": "24",
          "DriverStandings": [
            {
              "position": "1", "points": "423.5", "wins": "7",
              "Driver": {"driverId": "norris", "permanentNumber": "4", "code": "NOR",
                         "givenName": "Lando", "familyName": "Norris", "nationality": "British"},
              "Constructors": [{"constructorId": "mclaren", "name": "McLaren", "nationality": "British"}]
            },
            {
              "position": "2", "points": "421", "wins": "7",
              "Driver": {"driverId": "max_verstappen", "permanentNumber": "33", "code": "VER",
                         "givenName": "Max", "familyName": "Verstappen", "nationality": "Dutch"},
              "Constructors": [{"constructorId": "red_bull", "name": "Red Bull", "nationality": "Austrian"}]
            }
          ]
        }
      ]
    }
  }
}
```

- [ ] **Step 2: Write the failing tests**

```python
# apps/worker/tests/test_jolpica.py
import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import respx

from f1_worker.sources.jolpica import JolpicaClient

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "driver_standings_2025.json").read_text())
URL = "https://api.jolpi.ca/ergast/f1/2025/driverStandings.json"


@respx.mock
async def test_parses_standings_with_fractional_points() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    rows = await JolpicaClient().driver_standings(2025)
    assert len(rows) == 2
    assert rows[0].driver_ref == "norris"
    assert rows[0].points == Decimal("423.5")
    assert rows[0].team_ref == "mclaren"
    assert rows[0].round == 24


@respx.mock
async def test_empty_standings_list_returns_empty() -> None:
    empty = {"MRData": {"StandingsTable": {"season": "2030", "StandingsLists": []}}}
    respx.get("https://api.jolpi.ca/ergast/f1/2030/driverStandings.json").mock(
        return_value=httpx.Response(200, json=empty)
    )
    assert await JolpicaClient().driver_standings(2030) == []


@respx.mock
async def test_retries_429_then_succeeds() -> None:
    route = respx.get(URL).mock(side_effect=[
        httpx.Response(429, headers={"Retry-After": "0"}),
        httpx.Response(200, json=FIXTURE),
    ])
    rows = await JolpicaClient(retry_wait=0).driver_standings(2025)
    assert route.call_count == 2 and len(rows) == 2


@respx.mock
async def test_persistent_500_raises_after_three_attempts() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await JolpicaClient(retry_wait=0).driver_standings(2025)
    assert route.call_count == 3
```

- [ ] **Step 3: Run to confirm failure**

Run: `uv run pytest apps/worker/tests/test_jolpica.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 4: Implement**

```python
# apps/worker/src/f1_worker/sources/jolpica.py
import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from f1_worker.resilience import CircuitBreaker


@dataclass(frozen=True)
class ParsedStanding:
    round: int
    position: int
    points: Decimal
    wins: int
    driver_ref: str
    driver_code: str | None
    given_name: str
    family_name: str
    number: int | None
    driver_nationality: str | None
    team_ref: str
    team_name: str
    team_nationality: str | None


class JolpicaClient:
    def __init__(
        self,
        base_url: str = "https://api.jolpi.ca/ergast/f1",
        client: httpx.AsyncClient | None = None,
        breaker: CircuitBreaker | None = None,
        retry_wait: float = 0.5,
        attempts: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        self.breaker = breaker or CircuitBreaker(failure_threshold=5, reset_seconds=60)
        self.retry_wait = retry_wait
        self.attempts = attempts

    async def _get_json(self, path: str) -> dict[str, Any]:
        async def attempt() -> dict[str, Any]:
            last: httpx.Response | None = None
            for n in range(self.attempts):
                resp = await self.client.get(f"{self.base_url}{path}")
                if resp.status_code not in (429, 500, 502, 503, 504):
                    resp.raise_for_status()
                    data: dict[str, Any] = resp.json()
                    return data
                last = resp
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else self.retry_wait * (2**n)
                if self.retry_wait == 0:
                    wait = 0
                if n < self.attempts - 1:
                    await asyncio.sleep(wait)
            assert last is not None
            last.raise_for_status()
            raise AssertionError("unreachable")

        return await self.breaker.call(attempt)

    async def driver_standings(self, year: int) -> list[ParsedStanding]:
        data = await self._get_json(f"/{year}/driverStandings.json")
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not lists:
            return []
        block = lists[0]
        rnd = int(block["round"])
        out: list[ParsedStanding] = []
        for item in block["DriverStandings"]:
            d, c = item["Driver"], item["Constructors"][0]
            number = d.get("permanentNumber")
            out.append(
                ParsedStanding(
                    round=rnd, position=int(item["position"]), points=Decimal(item["points"]),
                    wins=int(item["wins"]), driver_ref=d["driverId"], driver_code=d.get("code"),
                    given_name=d["givenName"], family_name=d["familyName"],
                    number=int(number) if number else None,
                    driver_nationality=d.get("nationality"), team_ref=c["constructorId"],
                    team_name=c["name"], team_nationality=c.get("nationality"),
                )
            )
        return out
```

- [ ] **Step 5: Run to confirm pass and commit**

Run: `uv run pytest apps/worker/tests/test_jolpica.py -v`
Expected: 4 passed.

```bash
git add -A && git commit -m "feat(worker): add Jolpica adapter with retries and fixtures"
```

---

### Task 11: Standings ingestion job (idempotent, concurrent-safe)

**Files:**
- Create: `apps/worker/src/f1_worker/jobs/{__init__,standings}.py`
- Test: `apps/worker/tests/test_standings_job.py`

**Interfaces:**
- Consumes: `JolpicaClient`, `record_run`, `f1_db` models.
- Produces: `async ingest_driver_standings(session_factory, client: JolpicaClient, year: int) -> int` returning the number of standing rows upserted. Upserts `Season`, `Team` (by `ref`), `Driver` (by `ref`), `DriverStanding` (by `season_id, round, driver_id`). Safe to run concurrently (all writes are `INSERT ... ON CONFLICT`). Records an `IngestionRun` with job name `standings`.

- [ ] **Step 1: Write the failing tests**

```python
# apps/worker/tests/test_standings_job.py
import asyncio
import json
from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_db.models import DriverStanding, IngestionRun
from f1_worker.jobs.standings import ingest_driver_standings
from f1_worker.sources.jolpica import JolpicaClient

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "driver_standings_2025.json").read_text())
URL = "https://api.jolpi.ca/ergast/f1/2025/driverStandings.json"


@pytest.fixture(autouse=True)
async def clean(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        await s.execute(text(
            "truncate driver_standings, drivers, teams, seasons, ingestion_runs cascade"))
        await s.commit()


@respx.mock
async def test_ingest_writes_rows_and_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    first = await ingest_driver_standings(session_factory, JolpicaClient(), 2025)
    second = await ingest_driver_standings(session_factory, JolpicaClient(), 2025)
    assert first == second == 2
    async with session_factory() as s:
        count = (await s.execute(select(func.count()).select_from(DriverStanding))).scalar_one()
    assert count == 2


@respx.mock
async def test_concurrent_runs_do_not_duplicate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    await asyncio.gather(*[
        ingest_driver_standings(session_factory, JolpicaClient(), 2025) for _ in range(5)
    ])
    async with session_factory() as s:
        count = (await s.execute(select(func.count()).select_from(DriverStanding))).scalar_one()
    assert count == 2


@respx.mock
async def test_empty_upstream_writes_nothing_and_succeeds(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    empty = {"MRData": {"StandingsTable": {"season": "2025", "StandingsLists": []}}}
    respx.get(URL).mock(return_value=httpx.Response(200, json=empty))
    assert await ingest_driver_standings(session_factory, JolpicaClient(), 2025) == 0
    async with session_factory() as s:
        run = (await s.execute(select(IngestionRun))).scalar_one()
    assert run.status == "success" and run.rows == 0


@respx.mock
async def test_upstream_failure_records_failed_run(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await ingest_driver_standings(session_factory, JolpicaClient(retry_wait=0), 2025)
    async with session_factory() as s:
        run = (await s.execute(select(IngestionRun))).scalar_one()
    assert run.status == "failed"
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest apps/worker/tests/test_standings_job.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

```python
# apps/worker/src/f1_worker/jobs/standings.py
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import Driver, DriverStanding, Season, Team
from f1_worker.runs import record_run
from f1_worker.sources.jolpica import JolpicaClient

SOURCE = "jolpica"


async def ingest_driver_standings(
    session_factory: async_sessionmaker[AsyncSession], client: JolpicaClient, year: int
) -> int:
    async with record_run(session_factory, "standings") as run:
        rows = await client.driver_standings(year)
        if not rows:
            run.rows = 0
            return 0
        async with session_factory() as s:
            await s.execute(
                insert(Season).values(id=uuid7(), year=year).on_conflict_do_nothing(
                    index_elements=["year"])
            )
            season_id = (await s.execute(select(Season.id).where(Season.year == year))).scalar_one()
            for r in rows:
                await s.execute(
                    insert(Team).values(
                        id=uuid7(), ref=r.team_ref, name=r.team_name,
                        nationality=r.team_nationality, source=SOURCE, ingested_at=utcnow(),
                    ).on_conflict_do_update(
                        index_elements=["ref"],
                        set_={"name": r.team_name, "nationality": r.team_nationality},
                    )
                )
                await s.execute(
                    insert(Driver).values(
                        id=uuid7(), ref=r.driver_ref, code=r.driver_code,
                        given_name=r.given_name, family_name=r.family_name, number=r.number,
                        nationality=r.driver_nationality, source=SOURCE, ingested_at=utcnow(),
                    ).on_conflict_do_update(
                        index_elements=["ref"],
                        set_={"code": r.driver_code, "number": r.number,
                              "given_name": r.given_name, "family_name": r.family_name},
                    )
                )
                driver_id = (await s.execute(select(Driver.id).where(Driver.ref == r.driver_ref))).scalar_one()
                team_id = (await s.execute(select(Team.id).where(Team.ref == r.team_ref))).scalar_one()
                stmt = insert(DriverStanding).values(
                    id=uuid7(), season_id=season_id, round=r.round, driver_id=driver_id,
                    team_id=team_id, position=r.position, points=r.points, wins=r.wins,
                    source=SOURCE, ingested_at=utcnow(),
                )
                await s.execute(stmt.on_conflict_do_update(
                    index_elements=["season_id", "round", "driver_id"],
                    set_={"position": r.position, "points": r.points, "wins": r.wins,
                          "team_id": team_id, "ingested_at": utcnow()},
                ))
            await s.commit()
        run.rows = len(rows)
        return len(rows)
```

- [ ] **Step 4: Run to confirm pass and commit**

Run: `uv run pytest apps/worker/tests -v`
Expected: all pass.

```bash
uv run ruff check apps/worker && uv run mypy apps/worker/src
git add -A && git commit -m "feat(worker): add idempotent driver standings ingestion"
```

---

### Task 12: Arq worker settings and schedule

**Files:**
- Create: `apps/worker/src/f1_worker/settings.py`
- Test: `apps/worker/tests/test_settings.py`

**Interfaces:**
- Produces: `WorkerSettings` (Arq class settings) with `functions = [standings_task]`, `cron_jobs` running `standings_task` every 30 minutes (minutes 0 and 30) with `unique=True`, `on_startup` building the engine and `JolpicaClient` in `ctx`, and `on_shutdown` disposing them. `async standings_task(ctx) -> int` ingests the current season.

- [ ] **Step 1: Write the failing test**

```python
# apps/worker/tests/test_settings.py
from f1_worker.settings import WorkerSettings, standings_task


def test_standings_scheduled_every_30_minutes_and_unique() -> None:
    job = next(j for j in WorkerSettings.cron_jobs if j.coroutine is standings_task)
    assert job.minute == {0, 30}
    assert job.unique is True


def test_standings_registered_as_function() -> None:
    assert standings_task in WorkerSettings.functions
```

- [ ] **Step 2: Run, then implement**

Run: `uv run pytest apps/worker/tests/test_settings.py -v` (Expected: FAIL.)

```python
# apps/worker/src/f1_worker/settings.py
from datetime import UTC, datetime
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from pydantic_settings import BaseSettings, SettingsConfigDict

from f1_db.session import make_engine, make_session_factory
from f1_worker.jobs.standings import ingest_driver_standings
from f1_worker.sources.jolpica import JolpicaClient


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://f1:f1@localhost:5432/f1"
    redis_url: str = "redis://localhost:6379/0"


async def standings_task(ctx: dict[str, Any]) -> int:
    year = datetime.now(UTC).year
    return await ingest_driver_standings(ctx["session_factory"], ctx["jolpica"], year)


async def on_startup(ctx: dict[str, Any]) -> None:
    cfg = Config()
    ctx["engine"] = make_engine(cfg.database_url)
    ctx["session_factory"] = make_session_factory(ctx["engine"])
    ctx["jolpica"] = JolpicaClient()


async def on_shutdown(ctx: dict[str, Any]) -> None:
    await ctx["jolpica"].client.aclose()
    await ctx["engine"].dispose()


class WorkerSettings:
    functions = [standings_task]
    cron_jobs = [cron(standings_task, minute={0, 30}, unique=True, run_at_startup=True)]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(Config().redis_url)
    max_tries = 3
    job_timeout = 120
```

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest apps/worker/tests/test_settings.py -v`
Expected: 2 passed.

```bash
git add -A && git commit -m "feat(worker): schedule standings ingestion with arq"
```

---

### Task 13: Contract package (OpenAPI export, typed client, drift check)

**Files:**
- Create: `apps/api/scripts/export_openapi.py`, `packages/contract/{package.json,tsconfig.json,src/index.ts}`
- Generated and committed: `packages/contract/openapi.json`, `packages/contract/src/schema.d.ts`
- Test: `apps/api/tests/test_openapi_export.py`

**Interfaces:**
- Produces: `@f1/contract` exporting `createApiClient(baseUrl: string, init?: { headers?: Record<string, string>; fetch?: typeof fetch }) -> Client<paths>` and the `paths`/`components` types. `pnpm contract` regenerates both files. CI fails if `git diff` is non-empty afterwards.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_openapi_export.py
import json
from pathlib import Path

from f1_api.main import create_app
from f1_api.config import Settings

SPEC = Path(__file__).resolve().parents[3] / "packages" / "contract" / "openapi.json"


def test_committed_openapi_matches_app() -> None:
    app = create_app(Settings())
    assert json.loads(SPEC.read_text()) == app.openapi()
```

- [ ] **Step 2: Write the export script and generate**

```python
# apps/api/scripts/export_openapi.py
import json
from pathlib import Path

from f1_api.config import Settings
from f1_api.main import create_app

OUT = Path(__file__).resolve().parents[3] / "packages" / "contract" / "openapi.json"

if __name__ == "__main__":
    spec = create_app(Settings()).openapi()
    OUT.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT}")
```

Note: the test compares parsed JSON, so key ordering does not matter. Run: `uv run python apps/api/scripts/export_openapi.py`.

- [ ] **Step 3: Write the contract package**

```json
// packages/contract/package.json
{
  "name": "@f1/contract",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "scripts": {
    "generate": "cd ../.. && uv run python apps/api/scripts/export_openapi.py && cd packages/contract && openapi-typescript openapi.json -o src/schema.d.ts",
    "typecheck": "tsc --noEmit",
    "lint": "tsc --noEmit",
    "test": "vitest run"
  },
  "dependencies": { "openapi-fetch": "^0.13.0" },
  "devDependencies": { "openapi-typescript": "^7.4.0", "typescript": "^5.6.0", "vitest": "^2.1.0" }
}
```

```json
// packages/contract/tsconfig.json
{ "extends": "../../tsconfig.base.json", "include": ["src"], "compilerOptions": { "noEmit": true } }
```

```ts
// packages/contract/src/index.ts
import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

export type { components, paths };
export type DriverStanding = components["schemas"]["DriverStandingOut"];
export type Freshness = components["schemas"]["FreshnessOut"];

export interface ApiClientInit {
  headers?: Record<string, string>;
  fetch?: typeof fetch;
}

export function createApiClient(baseUrl: string, init: ApiClientInit = {}) {
  return createClient<paths>({ baseUrl, ...init });
}
```

- [ ] **Step 4: Generate types and add a client test**

Run: `pnpm install && pnpm --filter @f1/contract generate`
Expected: `packages/contract/src/schema.d.ts` exists and mentions `getDriverStandings`.

```ts
// packages/contract/src/index.test.ts
import { describe, expect, it } from "vitest";
import { createApiClient } from "./index";

describe("createApiClient", () => {
  it("calls the typed standings endpoint with the season query", async () => {
    let url = "";
    const client = createApiClient("http://api.test", {
      fetch: async (req) => {
        url = (req as Request).url;
        return new Response("[]", { headers: { "content-type": "application/json" } });
      },
    });
    const { data } = await client.GET("/v1/standings/drivers", { params: { query: { season: 2025 } } });
    expect(url).toBe("http://api.test/v1/standings/drivers?season=2025");
    expect(data).toEqual([]);
  });
});
```

Run: `pnpm --filter @f1/contract test` (Expected: 1 passed) and `uv run pytest apps/api/tests/test_openapi_export.py -v` (Expected: 1 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(contract): generate typed client from openapi with drift test"
```

---

### Task 14: Design system package (`@f1/ui`)

**Files:**
- Create: `packages/ui/{package.json,tsconfig.json,vitest.config.ts}`, `src/styles/tokens.css`, `src/lib/cn.ts`, `src/components/{button,card,timing-tower-row,data-table,tabs,dialog,command-palette}.tsx`, `src/index.ts`, `.storybook/{main.ts,preview.ts}`, `src/components/*.stories.tsx`
- Test: `src/components/{button,timing-tower-row}.test.tsx`

**Interfaces:**
- Produces:
  - CSS tokens: `--color-carbon-950 #0B0B0D`, `--color-carbon-900 #121216`, `--color-carbon-800 #1A1A1F`, `--color-brand #E10600`, `--color-timing-purple #B138DD`, `--color-timing-green #00D26A`, `--color-timing-yellow #FFD60A`, and `--team` (default equals brand). Fonts `--font-display`, `--font-sans`, `--font-mono`.
  - `<Button variant="primary" | "secondary" | "ghost" size="sm" | "md">`, `<Card>`, `<TimingTowerRow position: number; code: string; name: string; value: string; delta?: string; teamColor?: string; sector?: "purple" | "green" | "yellow" | "none" />`, `<DataTable>`, `Tabs*`, `Dialog*`, `<CommandPalette items onSelect>`.
  - Utility `cn(...classes)`.
  - Setting `style={{"--team": "#FF8000"}}` on any ancestor retheme accents.

- [ ] **Step 1: Write `packages/ui/package.json` and configs**

```json
{
  "name": "@f1/ui",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": { ".": "./src/index.ts", "./styles.css": "./src/styles/tokens.css" },
  "scripts": {
    "storybook": "storybook dev -p 6006",
    "build": "storybook build",
    "typecheck": "tsc --noEmit",
    "lint": "tsc --noEmit",
    "test": "vitest run"
  },
  "dependencies": {
    "@radix-ui/react-dialog": "^1.1.2",
    "@radix-ui/react-slot": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.1",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.0.4",
    "tailwind-merge": "^2.5.4"
  },
  "peerDependencies": { "react": "^19.0.0", "react-dom": "^19.0.0" },
  "devDependencies": {
    "@storybook/addon-a11y": "^8.4.0",
    "@storybook/react-vite": "^8.4.0",
    "@tailwindcss/vite": "^4.0.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "jsdom": "^25.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "storybook": "^8.4.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  }
}
```

```json
// packages/ui/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "include": ["src", ".storybook"],
  "compilerOptions": { "jsx": "react-jsx", "noEmit": true, "types": ["vitest/globals", "@testing-library/jest-dom"] }
}
```

```ts
// packages/ui/vitest.config.ts
import { defineConfig } from "vitest/config";
export default defineConfig({
  test: { environment: "jsdom", globals: true, setupFiles: ["./vitest.setup.ts"] },
});
```

```ts
// packages/ui/vitest.setup.ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 2: Write tokens**

```css
/* packages/ui/src/styles/tokens.css */
@import "tailwindcss";

@theme {
  --color-carbon-950: #0b0b0d;
  --color-carbon-900: #121216;
  --color-carbon-800: #1a1a1f;
  --color-carbon-700: #26262d;
  --color-carbon-500: #5c5c68;
  --color-carbon-200: #d4d4dc;
  --color-carbon-50: #f5f5f7;
  --color-brand: #e10600;
  --color-timing-purple: #b138dd;
  --color-timing-green: #00d26a;
  --color-timing-yellow: #ffd60a;
  --color-team: var(--team, #e10600);
  --font-display: "Barlow Condensed", "Arial Narrow", sans-serif;
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --radius-card: 14px;
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}

:root { color-scheme: dark; --team: #e10600; }

html, body { background: var(--color-carbon-950); color: var(--color-carbon-50); font-family: var(--font-sans); }

.tabular { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

- [ ] **Step 3: Write the failing component tests**

```tsx
// packages/ui/src/components/button.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { Button } from "./button";

describe("Button", () => {
  it("renders children and fires onClick", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Go</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("does not fire when disabled", async () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Go</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(onClick).not.toHaveBeenCalled();
  });
});
```

```tsx
// packages/ui/src/components/timing-tower-row.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TimingTowerRow } from "./timing-tower-row";

describe("TimingTowerRow", () => {
  it("shows position, code, and value in an accessible row", () => {
    render(<TimingTowerRow position={1} code="NOR" name="Lando Norris" value="423.5" />);
    const row = screen.getByRole("row", { name: /1 NOR Lando Norris 423.5/ });
    expect(row).toBeInTheDocument();
  });

  it("applies the purple sector class", () => {
    render(<TimingTowerRow position={2} code="VER" name="Max Verstappen" value="1:21.3" sector="purple" />);
    expect(screen.getByTestId("sector-bar")).toHaveClass("bg-timing-purple");
  });

  it("renders fractional values verbatim", () => {
    render(<TimingTowerRow position={3} code="PIA" name="Oscar Piastri" value="12.5" />);
    expect(screen.getByText("12.5")).toBeInTheDocument();
  });
});
```

Add `@testing-library/user-event` (`^14.5.0`) to `devDependencies`.

- [ ] **Step 4: Run to confirm failure**

Run: `pnpm install && pnpm --filter @f1/ui test`
Expected: FAIL (modules missing).

- [ ] **Step 5: Implement components**

```ts
// packages/ui/src/lib/cn.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

```tsx
// packages/ui/src/components/button.tsx
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "../lib/cn";

const button = cva(
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-transform duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-team disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
  {
    variants: {
      variant: {
        primary: "bg-team text-white hover:brightness-110",
        secondary: "bg-carbon-800 text-carbon-50 hover:bg-carbon-700",
        ghost: "text-carbon-200 hover:bg-carbon-800",
      },
      size: { sm: "h-8 px-3 text-sm", md: "h-10 px-4 text-sm" },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp ref={ref} className={cn(button({ variant, size }), className)} {...props} />;
  },
);
Button.displayName = "Button";
```

```tsx
// packages/ui/src/components/card.tsx
import * as React from "react";
import { cn } from "../lib/cn";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-[var(--radius-card)] border border-carbon-700 bg-carbon-900 p-5", className)}
      {...props}
    />
  );
}
```

```tsx
// packages/ui/src/components/timing-tower-row.tsx
import { cn } from "../lib/cn";

export interface TimingTowerRowProps {
  position: number;
  code: string;
  name: string;
  value: string;
  delta?: string;
  teamColor?: string;
  sector?: "purple" | "green" | "yellow" | "none";
}

const sectorClass = {
  purple: "bg-timing-purple",
  green: "bg-timing-green",
  yellow: "bg-timing-yellow",
  none: "bg-carbon-700",
} as const;

export function TimingTowerRow({
  position, code, name, value, delta, teamColor, sector = "none",
}: TimingTowerRowProps) {
  return (
    <div
      role="row"
      aria-label={`${position} ${code} ${name} ${value}`}
      className="grid grid-cols-[2.5rem_4px_1fr_auto_auto] items-center gap-3 border-b border-carbon-800 px-3 py-2 transition-transform duration-200 ease-[var(--ease-spring)]"
    >
      <span className="tabular text-right text-carbon-200">{position}</span>
      <span aria-hidden className="h-6 w-1 rounded" style={{ background: teamColor ?? "var(--team)" }} />
      <span className="flex items-baseline gap-2">
        <span className="font-[var(--font-display)] text-xl font-bold tracking-wide">{code}</span>
        <span className="text-sm text-carbon-200">{name}</span>
      </span>
      <span className="tabular">{value}</span>
      {delta ? <span className="tabular text-xs text-carbon-500">{delta}</span> : <span />}
      <span data-testid="sector-bar" aria-hidden className={cn("col-span-5 h-0.5 rounded", sectorClass[sector])} />
    </div>
  );
}
```

```tsx
// packages/ui/src/components/data-table.tsx
import * as React from "react";
import { cn } from "../lib/cn";

export function DataTable({ className, ...props }: React.TableHTMLAttributes<HTMLTableElement>) {
  return <table className={cn("w-full text-left text-sm [&_td]:py-2 [&_th]:py-2 [&_th]:text-carbon-500", className)} {...props} />;
}
```

```tsx
// packages/ui/src/components/tabs.tsx
import * as TabsPrimitive from "@radix-ui/react-tabs";
import * as React from "react";
import { cn } from "../lib/cn";

export const Tabs = TabsPrimitive.Root;
export const TabsContent = TabsPrimitive.Content;

export function TabsList({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.List>) {
  return <TabsPrimitive.List className={cn("flex gap-1 border-b border-carbon-700", className)} {...props} />;
}

export function TabsTrigger({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn("px-4 py-2 text-carbon-200 data-[state=active]:border-b-2 data-[state=active]:border-team data-[state=active]:text-white", className)}
      {...props}
    />
  );
}
```

```tsx
// packages/ui/src/components/dialog.tsx
import * as DialogPrimitive from "@radix-ui/react-dialog";
import * as React from "react";
import { cn } from "../lib/cn";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogTitle = DialogPrimitive.Title;
export const DialogDescription = DialogPrimitive.Description;

export function DialogContent({ className, children, ...props }: React.ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 bg-black/70" />
      <DialogPrimitive.Content
        className={cn("fixed left-1/2 top-1/2 w-[min(32rem,92vw)] -translate-x-1/2 -translate-y-1/2 rounded-[var(--radius-card)] border border-carbon-700 bg-carbon-900 p-6", className)}
        {...props}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
```

```tsx
// packages/ui/src/components/command-palette.tsx
"use client";
import { Command } from "cmdk";
import * as React from "react";

export interface CommandItem { id: string; label: string; hint?: string }
export interface CommandPaletteProps {
  items: CommandItem[];
  onSelect: (item: CommandItem) => void;
}

export function CommandPalette({ items, onSelect }: CommandPaletteProps) {
  const [open, setOpen] = React.useState(false);
  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);
  return (
    <Command.Dialog open={open} onOpenChange={setOpen} label="Command palette">
      <Command.Input placeholder="Search drivers, races, sessions" />
      <Command.List>
        <Command.Empty>No results.</Command.Empty>
        {items.map((item) => (
          <Command.Item key={item.id} value={item.label} onSelect={() => { onSelect(item); setOpen(false); }}>
            {item.label}
            {item.hint ? <span className="ml-auto text-carbon-500">{item.hint}</span> : null}
          </Command.Item>
        ))}
      </Command.List>
    </Command.Dialog>
  );
}
```

```ts
// packages/ui/src/index.ts
export * from "./lib/cn";
export * from "./components/button";
export * from "./components/card";
export * from "./components/timing-tower-row";
export * from "./components/data-table";
export * from "./components/tabs";
export * from "./components/dialog";
export * from "./components/command-palette";
```

- [ ] **Step 6: Storybook config and stories**

```ts
// packages/ui/.storybook/main.ts
import type { StorybookConfig } from "@storybook/react-vite";
import tailwindcss from "@tailwindcss/vite";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.tsx"],
  addons: ["@storybook/addon-a11y"],
  framework: "@storybook/react-vite",
  viteFinal: async (cfg) => ({ ...cfg, plugins: [...(cfg.plugins ?? []), tailwindcss()] }),
};
export default config;
```

```ts
// packages/ui/.storybook/preview.ts
import type { Preview } from "@storybook/react";
import "../src/styles/tokens.css";

const preview: Preview = {
  parameters: { backgrounds: { default: "carbon", values: [{ name: "carbon", value: "#0b0b0d" }] } },
};
export default preview;
```

```tsx
// packages/ui/src/components/timing-tower-row.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { TimingTowerRow } from "./timing-tower-row";

const meta: Meta<typeof TimingTowerRow> = { component: TimingTowerRow };
export default meta;

export const Leader: StoryObj<typeof TimingTowerRow> = {
  args: { position: 1, code: "NOR", name: "Lando Norris", value: "423.5", teamColor: "#FF8000", sector: "purple" },
};
export const Chaser: StoryObj<typeof TimingTowerRow> = {
  args: { position: 2, code: "VER", name: "Max Verstappen", value: "421", delta: "-2.5", teamColor: "#3671C6", sector: "green" },
};
```

```tsx
// packages/ui/src/components/button.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";

const meta: Meta<typeof Button> = { component: Button, args: { children: "Button" } };
export default meta;
export const Primary: StoryObj<typeof Button> = {};
export const Secondary: StoryObj<typeof Button> = { args: { variant: "secondary" } };
export const Ghost: StoryObj<typeof Button> = { args: { variant: "ghost" } };
```

Add equivalent one-story files for `card`, `tabs`, `dialog`, `data-table`, `command-palette` following the same shape (default export meta, at least one named story rendering the component with realistic F1 content).

- [ ] **Step 7: Run to confirm pass and commit**

Run: `pnpm --filter @f1/ui test && pnpm --filter @f1/ui typecheck && pnpm --filter @f1/ui build`
Expected: 5 tests pass, typecheck clean, Storybook builds to `storybook-static/`.

```bash
git add -A && git commit -m "feat(ui): add Pit Wall design tokens, components and storybook"
```

---

### Task 15: Web app, Better Auth and the `/standings` slice

**Files:**
- Create: `apps/web/{package.json,tsconfig.json,next.config.ts,postcss.config.mjs}`, `src/app/{layout.tsx,page.tsx,globals.css}`, `src/app/(auth)/sign-in/page.tsx`, `src/app/(auth)/sign-up/page.tsx`, `src/app/standings/page.tsx`, `src/app/api/auth/[...all]/route.ts`, `src/lib/{auth.ts,auth-client.ts,api.ts,env.ts}`, `src/proxy.ts`, `src/components/{standings-table.tsx,freshness-label.tsx}`
- Test: `apps/web/src/components/{standings-table.test.tsx,freshness-label.test.tsx}`, `apps/web/src/lib/safe-next.test.ts`

**Interfaces:**
- Consumes: `@f1/contract` (`createApiClient`, `DriverStanding`, `Freshness`), `@f1/ui`.
- Produces:
  - `src/lib/auth.ts` exporting `auth` (Better Auth server instance with email/password, Google and GitHub providers when env present, `jwt()` plugin, Postgres pool pointing at schema `auth`).
  - `src/lib/api.ts` exporting `getApi(token?: string)` which builds a client from `API_BASE_URL`.
  - `src/lib/safe-next.ts` exporting `safeNext(next: string | null): string` that only allows same-origin paths beginning with a single `/` and falls back to `/standings`.
  - `src/proxy.ts` redirecting unauthenticated requests for `/standings` to `/sign-in?next=/standings`.
  - `<StandingsTable rows: DriverStanding[] />` and `<FreshnessLabel lastSuccessAt: string | null now?: Date />` ("Updated 5 min ago", or "Data may be stale" when over 2 hours old, or "No data yet" when null).

- [ ] **Step 1: Write `apps/web/package.json` and config**

```json
{
  "name": "@f1/web",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "test": "vitest run",
    "e2e": "playwright test"
  },
  "dependencies": {
    "@f1/contract": "workspace:*",
    "@f1/ui": "workspace:*",
    "better-auth": "^1.3.0",
    "next": "^16.0.0",
    "pg": "^8.13.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.49.0",
    "@tailwindcss/postcss": "^4.0.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.0",
    "@types/node": "^22.0.0",
    "@types/pg": "^8.11.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "eslint": "^9.0.0",
    "eslint-config-next": "^16.0.0",
    "jsdom": "^25.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  }
}
```

```ts
// apps/web/next.config.ts
import type { NextConfig } from "next";

const config: NextConfig = {
  transpilePackages: ["@f1/ui", "@f1/contract"],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' " +
              (process.env.API_BASE_URL ?? "http://localhost:8000"),
          },
        ],
      },
    ];
  },
};
export default config;
```

```json
// apps/web/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "jsx": "preserve", "noEmit": true, "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }, "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["next-env.d.ts", "src", "e2e", ".next/types/**/*.ts"]
}
```

```js
// apps/web/postcss.config.mjs
export default { plugins: { "@tailwindcss/postcss": {} } };
```

```ts
// apps/web/vitest.config.ts
import { defineConfig } from "vitest/config";
import path from "node:path";
export default defineConfig({
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  test: { environment: "jsdom", globals: true, setupFiles: ["./vitest.setup.ts"], exclude: ["e2e/**", "node_modules/**"] },
});
```

```ts
// apps/web/vitest.setup.ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 2: Write the failing unit tests**

```ts
// apps/web/src/lib/safe-next.test.ts
import { describe, expect, it } from "vitest";
import { safeNext } from "./safe-next";

describe("safeNext", () => {
  it("allows same-origin paths", () => expect(safeNext("/standings")).toBe("/standings"));
  it("falls back for null", () => expect(safeNext(null)).toBe("/standings"));
  it.each(["https://evil.com", "//evil.com", "/\\evil.com", "javascript:alert(1)"])(
    "rejects %s", (bad) => expect(safeNext(bad)).toBe("/standings"),
  );
});
```

```tsx
// apps/web/src/components/freshness-label.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FreshnessLabel } from "./freshness-label";

const now = new Date("2026-10-29T12:00:00Z");

describe("FreshnessLabel", () => {
  it("shows minutes ago", () => {
    render(<FreshnessLabel lastSuccessAt="2026-10-29T11:55:00Z" now={now} />);
    expect(screen.getByText("Updated 5 min ago")).toBeInTheDocument();
  });
  it("warns when stale over 2 hours", () => {
    render(<FreshnessLabel lastSuccessAt="2026-10-29T08:00:00Z" now={now} />);
    expect(screen.getByText(/may be stale/i)).toBeInTheDocument();
  });
  it("handles no data", () => {
    render(<FreshnessLabel lastSuccessAt={null} now={now} />);
    expect(screen.getByText("No data yet")).toBeInTheDocument();
  });
});
```

```tsx
// apps/web/src/components/standings-table.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { DriverStanding } from "@f1/contract";
import { StandingsTable } from "./standings-table";

const row = (over: Partial<DriverStanding> = {}): DriverStanding => ({
  position: 1, points: 423.5, wins: 7, season: 2025, round: 24, updated_at: "2026-10-29T12:00:00Z",
  driver: { id: "d1", code: "NOR", given_name: "Lando", family_name: "Norris", number: 4 },
  team: { id: "t1", name: "McLaren" }, ...over,
});

describe("StandingsTable", () => {
  it("renders fractional points exactly", () => {
    render(<StandingsTable rows={[row()]} />);
    expect(screen.getByText("423.5")).toBeInTheDocument();
  });
  it("renders an empty state", () => {
    render(<StandingsTable rows={[]} />);
    expect(screen.getByText(/no standings/i)).toBeInTheDocument();
  });
  it("falls back to family name when code is missing", () => {
    render(<StandingsTable rows={[row({ driver: { id: "d", code: null, given_name: "A", family_name: "Zed", number: null } })]} />);
    expect(screen.getByText("ZED")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run to confirm failure**

Run: `pnpm install && pnpm --filter @f1/web test`
Expected: FAIL (modules missing).

- [ ] **Step 4: Implement the pure pieces**

```ts
// apps/web/src/lib/safe-next.ts
export function safeNext(next: string | null): string {
  const fallback = "/standings";
  if (!next) return fallback;
  if (!next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return fallback;
  return next;
}
```

```tsx
// apps/web/src/components/freshness-label.tsx
export function FreshnessLabel({ lastSuccessAt, now = new Date() }: { lastSuccessAt: string | null; now?: Date }) {
  if (!lastSuccessAt) return <span className="text-carbon-500">No data yet</span>;
  const minutes = Math.max(0, Math.round((now.getTime() - new Date(lastSuccessAt).getTime()) / 60000));
  if (minutes > 120) return <span className="text-timing-yellow">Data may be stale</span>;
  const text = minutes < 1 ? "Updated just now" : `Updated ${minutes} min ago`;
  return <span className="text-carbon-500">{text}</span>;
}
```

```tsx
// apps/web/src/components/standings-table.tsx
import type { DriverStanding } from "@f1/contract";
import { TimingTowerRow } from "@f1/ui";

export function StandingsTable({ rows }: { rows: DriverStanding[] }) {
  if (rows.length === 0) return <p className="text-carbon-500">No standings available yet.</p>;
  return (
    <div role="table" aria-label="Driver standings">
      {rows.map((r) => (
        <TimingTowerRow
          key={r.driver.id}
          position={r.position}
          code={(r.driver.code ?? r.driver.family_name.slice(0, 3)).toUpperCase().slice(0, r.driver.code ? 3 : 99)}
          name={`${r.driver.given_name} ${r.driver.family_name}`}
          value={String(r.points)}
          delta={`${r.wins}W`}
        />
      ))}
    </div>
  );
}
```

Note for the "falls back to family name" test: the code expression above yields `"ZED"` for family name `Zed`. If you prefer clarity, replace with `const code = (r.driver.code ?? r.driver.family_name).toUpperCase();` and pass `code`.

- [ ] **Step 5: Run to confirm pass**

Run: `pnpm --filter @f1/web test`
Expected: 10 passed.

- [ ] **Step 6: Implement auth and pages**

```ts
// apps/web/src/lib/env.ts
import { z } from "zod";

const schema = z.object({
  API_BASE_URL: z.string().url().default("http://localhost:8000"),
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url(),
  AUTH_DATABASE_URL: z.string().min(1),
  GOOGLE_CLIENT_ID: z.string().optional(),
  GOOGLE_CLIENT_SECRET: z.string().optional(),
  GITHUB_CLIENT_ID: z.string().optional(),
  GITHUB_CLIENT_SECRET: z.string().optional(),
});

export const env = schema.parse(process.env);
```

```ts
// apps/web/src/lib/auth.ts
import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins";
import { nextCookies } from "better-auth/next-js";
import { Pool } from "pg";
import { env } from "./env";

export const auth = betterAuth({
  database: new Pool({ connectionString: env.AUTH_DATABASE_URL }),
  secret: env.BETTER_AUTH_SECRET,
  baseURL: env.BETTER_AUTH_URL,
  emailAndPassword: { enabled: true, requireEmailVerification: false, minPasswordLength: 10 },
  socialProviders: {
    ...(env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET
      ? { google: { clientId: env.GOOGLE_CLIENT_ID, clientSecret: env.GOOGLE_CLIENT_SECRET } } : {}),
    ...(env.GITHUB_CLIENT_ID && env.GITHUB_CLIENT_SECRET
      ? { github: { clientId: env.GITHUB_CLIENT_ID, clientSecret: env.GITHUB_CLIENT_SECRET } } : {}),
  },
  rateLimit: { enabled: true, window: 60, max: 30 },
  plugins: [jwt({ jwt: { issuer: env.BETTER_AUTH_URL, expirationTime: "10m" } }), nextCookies()],
});
```

```ts
// apps/web/src/lib/auth-client.ts
import { createAuthClient } from "better-auth/react";
export const authClient = createAuthClient();
```

```ts
// apps/web/src/app/api/auth/[...all]/route.ts
import { toNextJsHandler } from "better-auth/next-js";
import { auth } from "@/lib/auth";
export const { GET, POST } = toNextJsHandler(auth);
```

```ts
// apps/web/src/lib/api.ts
import { createApiClient } from "@f1/contract";
import { env } from "./env";

export function getApi(token?: string) {
  return createApiClient(env.API_BASE_URL, token ? { headers: { Authorization: `Bearer ${token}` } } : {});
}
```

```ts
// apps/web/src/proxy.ts
import { getSessionCookie } from "better-auth/cookies";
import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  if (!getSessionCookie(request)) {
    const url = new URL("/sign-in", request.url);
    url.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = { matcher: ["/standings"] };
```

```tsx
// apps/web/src/app/layout.tsx
import "@f1/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "F1 Insight Hub",
  description: "Live F1 data, telemetry, predictions and fantasy. Unofficial, not affiliated with Formula 1.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="mx-auto max-w-4xl p-6">{children}</main>
      </body>
    </html>
  );
}
```

```css
/* apps/web/src/app/globals.css */
@source "../../../../packages/ui/src";
```

```tsx
// apps/web/src/app/page.tsx
import Link from "next/link";
import { Button } from "@f1/ui";

export default function Home() {
  return (
    <section className="space-y-6 py-16">
      <h1 className="font-[var(--font-display)] text-6xl font-extrabold tracking-wide">F1 INSIGHT HUB</h1>
      <p className="text-carbon-200">Standings, telemetry, predictions, and fantasy. Rebuilt from zero.</p>
      <Button asChild><Link href="/standings">View standings</Link></Button>
    </section>
  );
}
```

```tsx
// apps/web/src/app/standings/page.tsx
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { FreshnessLabel } from "@/components/freshness-label";
import { StandingsTable } from "@/components/standings-table";
import { auth } from "@/lib/auth";
import { getApi } from "@/lib/api";

export default async function StandingsPage() {
  const h = await headers();
  const session = await auth.api.getSession({ headers: h });
  if (!session) redirect("/sign-in?next=/standings");
  const { token } = await auth.api.getToken({ headers: h });
  const api = getApi(token);
  const [standings, fresh] = await Promise.all([
    api.GET("/v1/standings/drivers", {}),
    api.GET("/v1/meta/freshness", {}),
  ]);
  const last = fresh.data?.find((f) => f.job === "standings")?.last_success_at ?? null;
  return (
    <section className="space-y-4">
      <header className="flex items-end justify-between">
        <h1 className="font-[var(--font-display)] text-4xl font-bold">Driver Standings</h1>
        <FreshnessLabel lastSuccessAt={last} />
      </header>
      <StandingsTable rows={standings.data ?? []} />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(auth)/sign-in/page.tsx
"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "@f1/ui";
import { authClient } from "@/lib/auth-client";
import { safeNext } from "@/lib/safe-next";

function Form() {
  const params = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  return (
    <form
      className="mx-auto mt-16 flex max-w-sm flex-col gap-3"
      onSubmit={async (e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        const { error } = await authClient.signIn.email({
          email: String(data.get("email")), password: String(data.get("password")),
        });
        if (error) return setError(error.message ?? "Sign in failed");
        router.push(safeNext(params.get("next")));
      }}
    >
      <h1 className="font-[var(--font-display)] text-3xl font-bold">Sign in</h1>
      <input name="email" type="email" required aria-label="Email" className="rounded-md bg-carbon-800 p-3" />
      <input name="password" type="password" required aria-label="Password" className="rounded-md bg-carbon-800 p-3" />
      {error ? <p role="alert" className="text-brand">{error}</p> : null}
      <Button type="submit">Sign in</Button>
      <a href="/sign-up" className="text-sm text-carbon-200 underline">Create an account</a>
    </form>
  );
}

export default function SignInPage() {
  return <Suspense><Form /></Suspense>;
}
```

```tsx
// apps/web/src/app/(auth)/sign-up/page.tsx
"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@f1/ui";
import { authClient } from "@/lib/auth-client";

export default function SignUpPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  return (
    <form
      className="mx-auto mt-16 flex max-w-sm flex-col gap-3"
      onSubmit={async (e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        const { error } = await authClient.signUp.email({
          name: String(data.get("name")), email: String(data.get("email")),
          password: String(data.get("password")),
        });
        if (error) return setError(error.message ?? "Sign up failed");
        router.push("/standings");
      }}
    >
      <h1 className="font-[var(--font-display)] text-3xl font-bold">Create account</h1>
      <input name="name" required aria-label="Name" className="rounded-md bg-carbon-800 p-3" />
      <input name="email" type="email" required aria-label="Email" className="rounded-md bg-carbon-800 p-3" />
      <input name="password" type="password" required minLength={10} aria-label="Password" className="rounded-md bg-carbon-800 p-3" />
      {error ? <p role="alert" className="text-brand">{error}</p> : null}
      <Button type="submit">Sign up</Button>
    </form>
  );
}
```

- [ ] **Step 7: Create Better Auth tables, run, verify manually**

```bash
set -a && source .env && set +a
pnpm --filter @f1/web exec better-auth migrate --config src/lib/auth.ts -y
make up && make migrate
pnpm --filter @f1/web build
```

Expected: tables appear in schema `auth` (`\dt auth.*`), and `next build` succeeds.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat(web): add Better Auth, standings page and auth proxy"
```

---

### Task 16: API JWT verification and protected route

**Files:**
- Create: `apps/api/src/f1_api/auth/{__init__,jwt.py}`, `apps/api/src/f1_api/routers/me.py`
- Modify: `apps/api/src/f1_api/main.py`
- Test: `apps/api/tests/test_auth.py`

**Interfaces:**
- Produces:
  - `Principal(user_id: str, email: str | None)`.
  - `JwtVerifier(jwks_url: str, issuer: str)` with `verify(token: str) -> Principal` raising `ProblemError(401, ...)` for expired, wrong issuer, bad signature, or malformed tokens. JWKS is fetched with `httpx` and cached for 5 minutes. Tokens use EdDSA or RS256.
  - Dependency `current_principal` (reads `Authorization: Bearer`), and `GET /v1/me` returning `{user_id, email}` (used to prove the chain; later phases rely on `current_principal`).

- [ ] **Step 1: Write the failing tests**

```python
# apps/api/tests/test_auth.py
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from f1_api.auth.jwt import JwtVerifier, Principal, current_principal
from f1_api.errors import install_error_handlers

ISSUER = "http://auth.test"


@pytest.fixture(scope="module")
def key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _token(key: rsa.RSAPrivateKey, **over: object) -> str:
    claims = {"sub": "u1", "email": "a@b.c", "iss": ISSUER, "exp": int(time.time()) + 300, **over}
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "k1"})


def _app(key: rsa.RSAPrivateKey) -> FastAPI:
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    jwk.update({"kid": "k1", "alg": "RS256", "use": "sig"})
    verifier = JwtVerifier("http://auth.test/jwks", ISSUER, jwks_loader=lambda: {"keys": [jwk]})
    app = FastAPI()
    app.state.verifier = verifier
    install_error_handlers(app)

    @app.get("/me")
    async def me(p: Principal = Depends(current_principal)) -> dict[str, str | None]:
        return {"user_id": p.user_id, "email": p.email}

    return app


async def _get(key: rsa.RSAPrivateKey, header: str | None) -> int:
    async with AsyncClient(transport=ASGITransport(app=_app(key)), base_url="http://t") as c:
        r = await c.get("/me", headers={"Authorization": header} if header else {})
        return r.status_code


async def test_valid_token_ok(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, f"Bearer {_token(key)}") == 200


async def test_missing_header_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, None) == 401


async def test_expired_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, f"Bearer {_token(key, exp=int(time.time()) - 10)}") == 401


async def test_wrong_issuer_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, f"Bearer {_token(key, iss='http://evil')}") == 401


async def test_garbage_token_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, "Bearer not-a-jwt") == 401


async def test_signed_with_other_key_401(key: rsa.RSAPrivateKey) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert await _get(key, f"Bearer {_token(other)}") == 401
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest apps/api/tests/test_auth.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

```python
# apps/api/src/f1_api/auth/jwt.py
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import Request

from f1_api.errors import ProblemError


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str | None


class JwtVerifier:
    def __init__(
        self, jwks_url: str, issuer: str,
        jwks_loader: Callable[[], dict[str, Any]] | None = None, ttl: float = 300.0,
    ) -> None:
        self.jwks_url, self.issuer, self.ttl = jwks_url, issuer, ttl
        self._loader = jwks_loader or self._fetch
        self._cache: dict[str, Any] | None = None
        self._fetched_at = 0.0

    def _fetch(self) -> dict[str, Any]:
        resp = httpx.get(self.jwks_url, timeout=5.0)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data

    def _jwks(self, force: bool = False) -> dict[str, Any]:
        if force or self._cache is None or time.monotonic() - self._fetched_at > self.ttl:
            self._cache = self._loader()
            self._fetched_at = time.monotonic()
        return self._cache

    def verify(self, token: str) -> Principal:
        unauthorized = ProblemError(401, "Unauthorized", "Invalid or expired token")
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            for force in (False, True):
                keys = {k["kid"]: k for k in self._jwks(force)["keys"]}
                if kid in keys:
                    break
            else:
                raise unauthorized
            key = jwt.PyJWK(keys[kid]).key
            claims = jwt.decode(
                token, key, algorithms=["EdDSA", "RS256"], issuer=self.issuer,
                options={"require": ["exp", "iss", "sub"]},
            )
        except ProblemError:
            raise
        except Exception as exc:
            raise unauthorized from exc
        return Principal(user_id=str(claims["sub"]), email=claims.get("email"))


def current_principal(request: Request) -> Principal:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ProblemError(401, "Unauthorized", "Missing bearer token")
    verifier: JwtVerifier = request.app.state.verifier
    return verifier.verify(token)
```

```python
# apps/api/src/f1_api/routers/me.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from f1_api.auth.jwt import Principal, current_principal

router = APIRouter(prefix="/v1", tags=["me"])


class MeOut(BaseModel):
    user_id: str
    email: str | None


@router.get("/me", response_model=MeOut, operation_id="getMe")
async def me(principal: Principal = Depends(current_principal)) -> MeOut:
    return MeOut(user_id=principal.user_id, email=principal.email)
```

In `main.py`, inside `lifespan` add `app.state.verifier = JwtVerifier(cfg.auth_jwks_url, cfg.auth_issuer)` (import from `f1_api.auth.jwt`), and include `me.router`. Regenerate the contract: `pnpm contract`.

- [ ] **Step 4: Run to confirm pass and commit**

Run: `uv run pytest apps/api/tests -v && pnpm contract && uv run pytest apps/api/tests/test_openapi_export.py -v`
Expected: all pass.

```bash
git add -A && git commit -m "feat(api): verify better-auth jwts and add /v1/me"
```

---

### Task 17: Observability (logs, traces, Sentry)

**Files:**
- Create: `apps/api/src/f1_api/{logging_setup,telemetry}.py`
- Modify: `apps/api/src/f1_api/main.py`, `apps/worker/src/f1_worker/settings.py`
- Test: `apps/api/tests/test_logging.py`

**Interfaces:**
- Produces: `configure_logging(environment: str)` (JSON lines via structlog with `request_id` bound by the middleware, human console output in `development`), `setup_telemetry(app, settings)` which, only when `otlp_endpoint` or `sentry_dsn` is set, wires OpenTelemetry (FastAPI and SQLAlchemy instrumentation, OTLP exporter) and Sentry. A no-op when unset so tests and local dev work offline.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_logging.py
import json
import logging

import structlog

from f1_api.logging_setup import configure_logging


def test_json_logs_include_request_id(capsys) -> None:  # type: ignore[no-untyped-def]
    configure_logging("production")
    structlog.contextvars.bind_contextvars(request_id="abc")
    structlog.get_logger().info("hello", job="standings")
    line = capsys.readouterr().out.strip().splitlines()[-1]
    data = json.loads(line)
    assert data["event"] == "hello"
    assert data["request_id"] == "abc"
    assert data["job"] == "standings"
    structlog.contextvars.clear_contextvars()
    logging.getLogger().handlers.clear()
```

- [ ] **Step 2: Run to confirm failure, then implement**

Run: `uv run pytest apps/api/tests/test_logging.py -v` (Expected: FAIL.)

```python
# apps/api/src/f1_api/logging_setup.py
import logging
import sys

import structlog


def configure_logging(environment: str) -> None:
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    renderer: structlog.types.Processor = (
        structlog.dev.ConsoleRenderer()
        if environment == "development"
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[*processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=False,
    )
```

```python
# apps/api/src/f1_api/telemetry.py
from fastapi import FastAPI

from f1_api.config import Settings


def setup_telemetry(app: FastAPI, settings: Settings) -> None:
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn, environment=settings.environment,
            traces_sample_rate=0.1, send_default_pii=False,
        )
    if settings.otlp_endpoint:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "f1-api"}))
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{settings.otlp_endpoint}/v1/traces"))
        )
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
```

Wire in `create_app`: call `configure_logging(cfg.environment)` and `setup_telemetry(app, cfg)` after creating the app. In `RequestIdMiddleware`, bind `structlog.contextvars.bind_contextvars(request_id=rid)` before calling the app and `clear_contextvars()` in a `finally`. In `f1_worker/settings.py` `on_startup`, initialise Sentry when `SENTRY_DSN` is present (same `sentry_sdk.init` call) and log `job` start and end from `record_run` using `structlog.get_logger().info("job_finished", job=job, status=...)`.

- [ ] **Step 3: Run to confirm pass**

Run: `uv run pytest apps/api/tests -v`
Expected: all pass.

- [ ] **Step 4: Document the alert and dashboard**

Create `docs/runbooks/ingestion-lag.md`:

```markdown
# Alert: ingestion lag

Trigger: `GET /v1/meta/freshness` reports `last_success_at` older than 2 hours for job `standings`
(checked every 5 minutes by the uptime monitor), or `last_status = failed` for 3 consecutive checks.

1. Open Sentry for `f1-worker` and find the latest `failed` ingestion error.
2. If upstream returns 429 or 5xx, wait: the circuit breaker retries after 60 s.
3. If the schema changed (parse error), fix `f1_worker.sources.jolpica` and redeploy the worker.
4. Users keep seeing the last good data with a "Data may be stale" label. No customer action needed.
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(obs): add structured logging, tracing, sentry and lag runbook"
```

---

### Task 18: CI/CD, containers, Terraform and end-to-end proof

**Files:**
- Create: `.github/workflows/{ci.yml,deploy.yml}`, `infra/docker/{api.Dockerfile,worker.Dockerfile}`, `infra/fly/{api.fly.toml,worker.fly.toml}`, `infra/terraform/{main.tf,variables.tf,outputs.tf}`, `apps/web/e2e/standings.spec.ts`, `apps/web/playwright.config.ts`, `lighthouserc.json`, `docs/adr/{0002-job-queue-arq.md,0003-auth-better-auth.md}`, `README.md`
- Test: Playwright E2E `apps/web/e2e/standings.spec.ts`

**Interfaces:**
- Produces: CI jobs `js`, `py`, `contract-drift`, `e2e`, `lighthouse`. Deploy workflow: on push to `main`, deploy api and worker to Fly (staging), web to Vercel (staging); promote to production on manual approval.

- [ ] **Step 1: Write the E2E test (it is the Phase 0 exit criterion)**

```ts
// apps/web/e2e/standings.spec.ts
import { expect, test } from "@playwright/test";

test("unauthenticated user is redirected to sign-in with next param", async ({ page }) => {
  await page.goto("/standings");
  await expect(page).toHaveURL(/\/sign-in\?next=%2Fstandings/);
});

test("sign up, return to standings, and see ingested data", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  await page.goto("/sign-up");
  await page.getByLabel("Name").fill("E2E User");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("correct-horse-battery");
  await page.getByRole("button", { name: "Sign up" }).click();
  await expect(page).toHaveURL(/\/standings/);
  await expect(page.getByRole("heading", { name: "Driver Standings" })).toBeVisible();
  await expect(page.getByRole("row").first()).toBeVisible();
  await expect(page.getByText(/Updated|stale|No data yet/)).toBeVisible();
});

test("open redirect via next param is ignored", async ({ page }) => {
  await page.goto("/sign-in?next=https://evil.com");
  await page.getByLabel("Email").fill("nobody@example.com");
  await page.getByLabel("Password").fill("wrong-password-123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).not.toHaveURL(/evil\.com/);
});
```

```ts
// apps/web/playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000", trace: "retain-on-failure" },
  webServer: process.env.E2E_BASE_URL ? undefined : {
    command: "pnpm start", url: "http://localhost:3000", reuseExistingServer: true, timeout: 120_000,
  },
});
```

- [ ] **Step 2: Seed script for E2E**

Create `apps/worker/scripts/seed_standings.py`:

```python
import asyncio
import os
from datetime import UTC, datetime

from f1_db.session import make_engine, make_session_factory
from f1_worker.jobs.standings import ingest_driver_standings
from f1_worker.sources.jolpica import JolpicaClient


async def main() -> None:
    engine = make_engine(os.environ["DATABASE_URL"])
    count = await ingest_driver_standings(
        make_session_factory(engine), JolpicaClient(), datetime.now(UTC).year - 1
    )
    print(f"seeded {count} rows")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

Note: if the current year has no data yet, the page shows the empty state, which the E2E tolerates via the `row`-or-label assertions. For a deterministic CI seed, run the script for last year and set `NEXT_PUBLIC`-free fallback by querying with `?season=` in a later phase.

Adjust the E2E assertion in CI by making the standings page accept `?season=` (read `searchParams.season`, pass it to the API) so the test navigates to `/standings?season=<last year>`. Implement: in `page.tsx` accept `searchParams: Promise<{ season?: string }>`, and call `api.GET("/v1/standings/drivers", { params: { query: { season: season ? Number(season) : undefined } } })`. Update the E2E sign-up redirect expectation to `/\/standings/` (unchanged) and add `await page.goto("/standings?season=" + (new Date().getFullYear() - 1))` before the row assertion.

- [ ] **Step 3: Write Dockerfiles**

```dockerfile
# infra/docker/api.Dockerfile
FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
RUN uv sync --frozen --no-dev --package f1-api
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "f1_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# infra/docker/worker.Dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/worker ./apps/worker
RUN uv sync --frozen --no-dev --package f1-worker
ENV PATH="/app/.venv/bin:$PATH"
CMD ["arq", "f1_worker.settings.WorkerSettings"]
```

```toml
# infra/fly/api.fly.toml
app = "f1-insight-api"
primary_region = "iad"
[build]
  dockerfile = "../docker/api.Dockerfile"
[deploy]
  release_command = "sh -c 'cd packages/db-py && alembic upgrade head'"
[http_service]
  internal_port = 8000
  force_https = true
  min_machines_running = 1
  [[http_service.checks]]
    path = "/readyz"
    interval = "15s"
    timeout = "3s"
```

```toml
# infra/fly/worker.fly.toml
app = "f1-insight-worker"
primary_region = "iad"
[build]
  dockerfile = "../docker/worker.Dockerfile"
[processes]
  worker = "arq f1_worker.settings.WorkerSettings"
```

- [ ] **Step 4: Write Terraform**

```hcl
# infra/terraform/variables.tf
variable "environment" { type = string }
variable "cloudflare_account_id" { type = string }
variable "upstash_email" { type = string }
variable "upstash_api_key" {
  type      = string
  sensitive = true
}
variable "neon_api_key" {
  type      = string
  sensitive = true
}
variable "vercel_api_token" {
  type      = string
  sensitive = true
}
variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}
```

```hcl
# infra/terraform/main.tf
terraform {
  required_providers {
    neon       = { source = "kislerdm/neon" }
    upstash    = { source = "upstash/upstash" }
    cloudflare = { source = "cloudflare/cloudflare" }
    vercel     = { source = "vercel/vercel" }
  }
}

provider "neon" { api_key = var.neon_api_key }
provider "upstash" {
  email   = var.upstash_email
  api_key = var.upstash_api_key
}
provider "cloudflare" { api_token = var.cloudflare_api_token }
provider "vercel" { api_token = var.vercel_api_token }

resource "neon_project" "db" {
  name       = "f1-insight-${var.environment}"
  pg_version = 16
}

resource "upstash_redis_database" "cache" {
  database_name = "f1-insight-${var.environment}"
  region        = "global"
  primary_region = "us-east-1"
  tls           = true
}

resource "cloudflare_r2_bucket" "telemetry" {
  account_id = var.cloudflare_account_id
  name       = "f1-telemetry-${var.environment}"
}

resource "vercel_project" "web" {
  name      = "f1-insight-web-${var.environment}"
  framework = "nextjs"
  root_directory = "apps/web"
}
```

```hcl
# infra/terraform/outputs.tf
output "database_uri" {
  value     = neon_project.db.connection_uri
  sensitive = true
}
output "redis_endpoint" { value = upstash_redis_database.cache.endpoint }
output "telemetry_bucket" { value = cloudflare_r2_bucket.telemetry.name }
```

Validate: `cd infra/terraform && terraform init -backend=false && terraform validate`. Expected: `Success! The configuration is valid.`

- [ ] **Step 5: Write CI workflow**

```yaml
# .github/workflows/ci.yml
name: ci
on:
  pull_request:
  push:
    branches: [main]
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  js:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm lint
      - run: pnpm test
      - run: pnpm build
        env:
          BETTER_AUTH_SECRET: ci-secret-ci-secret-ci-secret-ci-secret
          BETTER_AUTH_URL: http://localhost:3000
          AUTH_DATABASE_URL: postgresql://f1:f1@localhost:5432/f1
  py:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with: { enable-cache: true }
      - run: uv sync --all-packages --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy packages apps
      - run: uv run pytest --cov=f1_core --cov-fail-under=90 packages/core-py
      - run: uv run pytest apps packages/db-py
  contract-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - uses: astral-sh/setup-uv@v4
      - run: pnpm install --frozen-lockfile && uv sync --all-packages --frozen
      - run: pnpm contract
      - run: git diff --exit-code packages/contract
  e2e:
    needs: [js, py]
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_DB: f1, POSTGRES_USER: f1, POSTGRES_PASSWORD: f1 }
        ports: ["5432:5432"]
        options: --health-cmd "pg_isready -U f1" --health-interval 5s --health-retries 10
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    env:
      DATABASE_URL: postgresql+asyncpg://f1:f1@localhost:5432/f1
      REDIS_URL: redis://localhost:6379/0
      BETTER_AUTH_SECRET: ci-secret-ci-secret-ci-secret-ci-secret
      BETTER_AUTH_URL: http://localhost:3000
      AUTH_DATABASE_URL: postgresql://f1:f1@localhost:5432/f1?options=-c%20search_path%3Dauth
      AUTH_ISSUER: http://localhost:3000
      AUTH_JWKS_URL: http://localhost:3000/api/auth/jwks
      API_BASE_URL: http://localhost:8000
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - uses: astral-sh/setup-uv@v4
      - run: pnpm install --frozen-lockfile && uv sync --all-packages --frozen
      - run: uv run --directory packages/db-py alembic upgrade head
      - run: pnpm --filter @f1/web exec better-auth migrate --config src/lib/auth.ts -y
      - run: uv run python apps/worker/scripts/seed_standings.py
      - run: uv run uvicorn f1_api.main:create_app --factory --port 8000 &
      - run: pnpm --filter @f1/web build
      - run: pnpm --filter @f1/web exec playwright install --with-deps chromium
      - run: pnpm --filter @f1/web e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with: { name: playwright-report, path: apps/web/playwright-report }
  lighthouse:
    needs: [e2e]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: treosh/lighthouse-ci-action@v12
        with:
          configPath: ./lighthouserc.json
          uploadArtifacts: true
```

```json
// lighthouserc.json
{
  "ci": {
    "collect": { "url": ["http://localhost:3000/"], "startServerCommand": "pnpm --filter @f1/web start", "numberOfRuns": 3 },
    "assert": {
      "assertions": {
        "largest-contentful-paint": ["error", { "maxNumericValue": 2000 }],
        "categories:accessibility": ["error", { "minScore": 0.95 }],
        "categories:performance": ["error", { "minScore": 0.9 }]
      }
    }
  }
}
```

- [ ] **Step 6: Write deploy workflow**

```yaml
# .github/workflows/deploy.yml
name: deploy
on:
  push:
    branches: [main]
jobs:
  staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --config infra/fly/api.fly.toml --remote-only
        env: { FLY_API_TOKEN: "${{ secrets.FLY_API_TOKEN }}" }
      - run: flyctl deploy --config infra/fly/worker.fly.toml --remote-only
        env: { FLY_API_TOKEN: "${{ secrets.FLY_API_TOKEN }}" }
      - run: curl --fail --retry 10 --retry-delay 6 https://f1-insight-api.fly.dev/readyz
  production:
    needs: staging
    runs-on: ubuntu-latest
    environment: production   # requires manual approval in GitHub settings
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --config infra/fly/api.fly.toml --remote-only --app f1-insight-api-prod
        env: { FLY_API_TOKEN: "${{ secrets.FLY_API_TOKEN }}" }
      - run: flyctl deploy --config infra/fly/worker.fly.toml --remote-only --app f1-insight-worker-prod
        env: { FLY_API_TOKEN: "${{ secrets.FLY_API_TOKEN }}" }
```

Web deploys through Vercel's Git integration (preview per PR, production on `main`). Fly rolls back automatically if the `/readyz` health check fails during deploy.

- [ ] **Step 7: Write ADRs and README**

`docs/adr/0002-job-queue-arq.md`:

```markdown
# ADR 0002: Arq for background jobs

Status: Accepted (2026-10-29)
Context: We need durable scheduled jobs with retries, async-native code, and Redis only.
Decision: Arq. Celery was rejected for sync-first design and operational weight.
Consequences: Cron is minute-granular; long jobs need explicit timeouts; no built-in dead-letter queue, so failed runs are recorded in `ingestion_runs` and alerted on.
```

`docs/adr/0003-auth-better-auth.md`:

```markdown
# ADR 0003: Better Auth in Next.js with JWT verification in the api

Status: Accepted (2026-10-29)
Decision: Better Auth owns sessions and users (schema `auth`). Its `jwt` plugin issues short-lived tokens, and the api verifies them against the JWKS endpoint.
Consequences: The api never touches passwords. Key rotation is handled by JWKS caching (5 min) with a forced refresh on unknown `kid`.
```

`README.md` (replaces the old one):

```markdown
# F1 Insight Hub

Unofficial F1 analytics platform. Not affiliated with Formula 1.

## Quick start
    cp .env.example .env
    make up && make migrate
    pnpm install && uv sync --all-packages
    make api      # terminal 1
    make worker   # terminal 2
    make web      # terminal 3

See `docs/superpowers/specs` and `docs/superpowers/plans` for design and roadmap.
```

- [ ] **Step 8: Run the whole suite locally**

Run:
```bash
make up && make migrate
uv run pytest
pnpm typecheck && pnpm test && pnpm build
uv run python apps/worker/scripts/seed_standings.py
pnpm --filter @f1/web e2e
```
Expected: all green. The E2E sign-up test lands on `/standings` and shows ingested rows (or the "No standings" state if upstream has nothing).

- [ ] **Step 9: Phase 0 exit check and commit**

Confirm each exit criterion: signed-in user views `/standings` from Postgres via the typed client; ingestion runs on schedule and `/v1/meta/freshness` reports it; CI gates all green on a PR; staging deploy succeeds.

```bash
git add -A && git commit -m "ci: add pipelines, containers, terraform and e2e proof for phase 0"
```

Open the PR `phase-0-foundation` to `main`.
