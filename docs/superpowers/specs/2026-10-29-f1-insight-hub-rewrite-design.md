# F1 Insight Hub: Full Rewrite Design

Date: 2026-10-29
Status: Draft for review

## 1. Goal and constraints

Rebuild F1 Insight Hub from scratch as a production-grade platform. No code from the existing frontend or backend is carried over. The old code is archived on a `legacy` branch for reference only.

- **Audience:** the author, F1 fans, and recruiters. It must be fast and polished enough to demo, and robust enough for public sign-ups.
- **Scope:** live race centre, telemetry compare, predictions, strategy sim, fantasy, news, accounts, favorites, notifications, and driver and team profiles.
- **Visual identity:** a unique F1 look called "Pit Wall" (see section 5).
- **Non-goals:** official licensed F1 live data, native mobile apps, paid subscriptions, and user-generated social content beyond fantasy leagues.

## 2. Decomposition

This is too large for a single plan. Each phase gets its own spec, plan and build cycle and ends deployable.

| Phase | Deliverable | Done when |
|---|---|---|
| 0. Foundation | Monorepo, CI/CD, design system with Storybook, contract pipeline, Postgres, Redis, worker and queue, auth, observability, preview deploys | A signed-in user sees a styled standings page fed by the full pipeline (ingest, DB, API, typed client, UI), deployed through CI |
| 1. Data and Race Centre | Calendar, standings, results, profiles, weather, live timing over SSE | A live session shows a timing tower with under 5 s lag |
| 2. Telemetry Lab | Lap compare, speed and throttle traces, track maps, sectors, pit stops | Two drivers' laps compare smoothly within the performance budget |
| 3. Predict and Strategy | Rating engine, Monte Carlo, strategy sim, AI notes, backtests | A backtest report is published and each prediction is reproducible by model version |
| 4. Fantasy | Leagues, picks, versioned scoring, leaderboards | A mock race weekend scores correctly end to end |
| 5. News and Social | Aggregated news, favorites, push and email notifications | Notifications deliver within one minute of the trigger event |

Phase 0 is first. Phases 1 and 2 form the first real product. Phases 3, 4 and 5 can follow in any order. Nothing from a later phase starts early.

## 3. Architecture

Chosen approach: monorepo with Next.js web, FastAPI api, Python worker, Postgres, and Redis. Python is retained because FastF1 telemetry and numpy/pandas simulation have no good TypeScript equivalent.

```
apps/web        Next.js (App Router, TypeScript, Tailwind v4)
apps/api        FastAPI (Python 3.12), versioned /v1, OpenAPI is the source of truth
apps/worker     Python ingestion and compute jobs
packages/contract   OpenAPI spec, generated TS client and Zod schemas
packages/ui         Design tokens, components, motion presets, Storybook
packages/core-py    Pure domain logic: ratings, Monte Carlo, strategy, scoring (no I/O)
infra/              Terraform, Docker, migrations
docs/               ADRs, runbooks, specs
```

### Data flow
1. The worker pulls from Jolpica (results, standings), FastF1 (laps, telemetry), OpenF1 (live timing) and the weather API, normalises into Postgres.
2. Telemetry is stored as compressed Parquet in S3-compatible object storage (Cloudflare R2), indexed in Postgres.
3. Redis caches hot reads and fans out live timing. The api streams it to clients over SSE.
4. The api serves typed endpoints and handles auth, fantasy and favorites writes. It never calls upstream sources on a user request.
5. The web app uses server components for first paint, and client components only for interactive charts and live data.

### Backend rules
- Layers: routers, services, repositories, domain core. Dependencies point inward only. `core-py` performs no I/O.
- Postgres 16, SQLAlchemy 2 (async), Alembic migrations (forward-only, reviewed, run in CI).
- Redis for cache (namespaced and versioned keys, stale-while-revalidate), rate limiting and pub/sub.
- Durable job queue (Arq or Celery) with retries, backoff, idempotency keys, dead-letter handling, and schedules tied to the race calendar (fast polling during sessions, slow otherwise).
- Live SSE has heartbeats, `Last-Event-ID` resume and per-connection limits.
- API standards: `/v1` versioning, cursor pagination, RFC 9457 problem-details errors, request IDs, ETags, idempotency keys on writes.
- Every endpoint has a Pydantic model that generates OpenAPI, then the TS client. There is no hand-written contract.

### Security
- Better Auth in Next.js (email and OAuth with Google and GitHub, email verification, rate-limited password reset). Secure httpOnly SameSite cookies and CSRF protection. A short-lived JWT is verified by the api. Role-based access for fantasy admin.
- Per-IP and per-user rate limits, strict CORS, security headers and CSP, input validation everywhere, upstream host allowlist.
- Secrets in a secret manager, never in the repo. Dependency and secret scanning in CI.
- GDPR basics: account deletion and data export.

### Reliability and observability
- Timeouts, retries and circuit breakers on all upstream calls. When a source is down, serve stale data with a visible "updated X ago" label.
- OpenTelemetry traces, structured JSON logs, Sentry, metrics dashboards.
- SLOs: p95 cached API read under 200 ms, LCP under 2.0 s, live-data lag under 5 s. Alerts on ingestion lag and error budget burn.
- Health and readiness endpoints, graceful shutdown, automated Postgres backups with a tested restore.

### Hosting (default)
Web on Vercel. Api and worker as containers on Fly.io or Railway. Postgres on Neon, Redis on Upstash, storage on Cloudflare R2. All defined in Terraform, and everything runs locally with `docker compose up`.

## 4. Data model

| Domain | Tables |
|---|---|
| Reference | `seasons`, `circuits`, `teams`, `drivers`, `driver_team_stints`, `races` |
| Sessions | `sessions`, `session_results`, `laps`, `stints`, `pit_stops`, `weather_samples` |
| Telemetry | `telemetry_index` (pointer to Parquet, keyed by session, driver, lap) |
| Live | Redis streams, flushed to Postgres at session end |
| Predictions | `rating_snapshots`, `prediction_runs`, `backtest_results` |
| Strategy | `strategy_simulations` (cached by parameter hash) |
| Users | `users`, `accounts`, `sessions`, `favorites`, `notification_prefs`, `push_subscriptions` |
| Fantasy | `leagues`, `league_members`, `fantasy_teams`, `fantasy_picks`, `fantasy_scores`, `scoring_rules` |
| News | `news_sources`, `articles` |

Conventions:
- UUIDv7 primary keys and `timestamptz` everywhere.
- Ingested rows carry `source` and `ingested_at` with natural-key unique constraints, so jobs are idempotent.
- Prediction runs are immutable and store their model version, so past predictions are reproducible and gradable.
- Fantasy scoring rules are versioned, so rule changes never rewrite past scores.

## 5. Design system: Pit Wall

- **Colour:** carbon base (`#0B0B0D`, elevated surfaces up to `#1A1A1F`), F1 red `#E10600` as the single brand accent. Fixed timing semantics: purple is overall best, green is personal best, yellow is slower, red is flag or alert. Team and driver pages retheme through a `--team` CSS variable. Dark by default, with an optional light "paddock" theme.
- **Type:** condensed bold display face for headings and driver names, a clean grotesque for UI, tabular mono for all times and numbers.
- **Signature elements:** a timing-tower component as the main idiom for standings, grids and fantasy leaderboards; sector-coloured lap bars; self-drawing track outlines with animated car position; a `Cmd+K` command palette for any driver, race or session; per-circuit hero art generated from real track geometry.
- **Motion:** 120 to 250 ms with spring easing, number tickers on lap times, animated reorders on the tower. All motion honours `prefers-reduced-motion`.
- **Layout:** 12-column responsive grid, left rail on desktop and top nav on mobile.
- **Delivery:** tokens defined once in `packages/ui` (CSS variables and typed TS export), a Storybook story for every component, with axe and visual-regression checks per story.
- **Frontend standards:** RSC-first with streaming and Suspense, WCAG 2.2 AA, keyboard navigation, mobile-first responsive, installable PWA, i18n-ready strings.

## 6. Quality gates

- **CI/CD (GitHub Actions):** lint, types (`tsc` strict, `mypy --strict`, `ruff`), unit, integration (Testcontainers for Postgres and Redis), contract tests (the generated client must match the OpenAPI spec), Playwright E2E, axe, visual regression, Lighthouse budget.
- **Domain core:** 90%+ coverage gate, plus property-based tests for scoring and simulation invariants.
- **Ingestion:** recorded upstream fixtures for deterministic tests, plus a nightly canary against the real APIs to detect schema drift.
- **Predictions:** backtests over past seasons gate any model change.
- **Deploys:** preview deploy per PR, then staging, then production with automatic rollback. Feature flags gate risky features.

## 7. Phase 0 scope (Foundation) in detail

In scope:
1. Monorepo scaffolding: Turborepo, pnpm, uv, strict lint and type configs, pre-commit hooks, ADR template.
2. `docker compose up` brings up web, api, worker, Postgres, Redis, and an S3-compatible store (MinIO).
3. `packages/ui`: tokens, base components (button, card, table, timing-tower row, tabs, dialog, command palette), Storybook, theming (`--team`), motion presets.
4. `packages/contract`: OpenAPI export from the api, generated TS client and Zod types, a CI check that fails on drift.
5. Api skeleton: layering, config, error format, request IDs, health and readiness, rate limiting, auth verification, one read endpoint (`GET /v1/standings`).
6. Database: Alembic baseline with reference tables (`seasons`, `drivers`, `teams`, `races`, `session_results`) and users and auth tables.
7. Worker skeleton: queue, scheduler, one ingestion job (Jolpica standings) with idempotency, retries and circuit breaker, recorded fixtures.
8. Auth: Better Auth sign-up, sign-in, OAuth, email verification, and a protected route.
9. Observability: OpenTelemetry, Sentry, structured logs, a dashboard and an alert for ingestion lag.
10. CI/CD pipeline with all gates from section 6, preview deploys, Terraform for staging and production.
11. A vertical slice page `/standings` that proves the full pipeline.
12. A `legacy` branch holding the old code, and removal of all old code from `main`.

Out of scope for Phase 0: live timing, telemetry, predictions, fantasy, news, notifications.

Exit criteria: a signed-in user views `/standings` served from Postgres via the typed client, ingestion runs on schedule and is visible in dashboards, and the whole stack deploys from CI to staging with all gates green.

## 8. Risks

1. **Upstream outages or limits.** FastF1, Jolpica and OpenF1 are free and unofficial. Mitigated by ingest-and-cache, circuit breakers, stale-with-label UI, and an adapter layer so any source can be swapped.
2. **Live timing licensing.** Official F1 live data is licensed. The app relies on OpenF1 (community), labels it unofficial, stays non-commercial, and shows a not-affiliated-with-Formula-1 disclaimer.
3. **Scope creep.** Phase gates are the guard.
4. **Cost.** Free and hobby tiers cover early use. Telemetry storage and live fan-out are the main drivers, so budgets and alerts are set in Phase 0.
5. **Rewrite regression.** Each phase spec includes a parity checklist against the old feature set. No old code is copied.

## 9. Open items

- Final domain name and brand name.
- Whether to use Arq or Celery (decided in the Phase 0 plan with a short ADR).
- Choice of display typeface (decided in the Phase 0 design-system task, subject to licensing).
