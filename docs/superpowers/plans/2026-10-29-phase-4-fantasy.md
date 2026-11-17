# Phase 4: Fantasy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let signed-in users build a fantasy F1 team under a budget, join or create leagues with invite codes, have picks lock automatically at qualifying, get scored after each race with versioned rules, and see timing-tower leaderboards.

**Architecture:** A pure `f1_core.fantasy` module owns scoring and budget validation (property tested). Postgres enforces integrity (unique picks, locks by timestamp). The api accepts picks only before `locks_at`, using the database clock. The worker scores finished races idempotently, writing `fantasy_scores` per team per race with the `rules_version` used. The web app shows the team builder, leagues and leaderboards.

**Tech Stack:** Phase 0 to 1 stack. No new infrastructure.

**Spec:** `docs/superpowers/specs/2026-10-29-f1-insight-hub-rewrite-design.md`. Depends on: Phases 0 and 1 (results, sessions, accounts).

## Global Constraints

- All write endpoints require a valid bearer JWT (`current_principal`) and are rate limited at 30 per minute per user.
- Time-based rules (lock) use database `now()` and UTC. Client clocks are never trusted.
- Scoring rules are versioned (`scoring_rules.version`, JSONB). A race is scored with the version active when it is scored and the version is stored on each score row. Changing rules never rewrites old scores; rescoring is an explicit admin action that writes new rows with a new version.
- Budget is stored in integer tenths of a million (e.g. `1000` equals 100.0M) to avoid float errors.
- Team size: exactly 5 drivers and 2 constructors. Budget cap: 100.0M. One captain among the drivers (double points).
- Invite codes: 8 characters from an unambiguous alphabet, unguessable (`secrets`), rate limited joins.
- Account deletion (Phase 5) must anonymise but keep league score history intact.

## Review Focus

1. Pick submitted exactly at or just after the lock time, or from two tabs at once: exactly one wins, post-lock requests get `409` with `locks_at`. (Task 3)
2. Over-budget teams, duplicate drivers, the wrong number of picks, or a captain not on the team: rejected with specific `422` codes. (Task 1, Task 3)
3. A driver is replaced mid-season or does not start (DNS), or the race is cancelled: scoring treats DNS as 0 and a cancelled race as no scoring round. (Task 2, Task 4)
4. Prices change between rounds: a team keeps its original purchase price as team value but must still fit the budget at current prices when edited. (Task 1, Task 3)
5. A user joins a league twice, joins with a wrong or expired code, or is removed: idempotent join, generic error that does not leak whether a league exists. (Task 5)
6. Scoring runs twice or concurrently for a race: no duplicated rows or double points. (Task 4)
7. Leaderboard ties: stable tiebreak by most race wins, then best single-race score, then earliest team creation. (Task 6)

---

## File Structure

```
packages/db-py/alembic/versions/0007_fantasy.py
packages/db-py/src/f1_db/models/fantasy.py
packages/core-py/src/f1_core/fantasy/{__init__,rules,scoring,budget,pricing,leaderboard}.py
packages/core-py/tests/fantasy/test_*.py
apps/worker/src/f1_worker/jobs/{fantasy_scoring,fantasy_pricing}.py
apps/api/src/f1_api/{schemas,services,routers}/{fantasy_teams,leagues,leaderboards,fantasy_admin}.py
apps/web/src/app/fantasy/{page.tsx,team/page.tsx,leagues/page.tsx,leagues/[id]/page.tsx}
apps/web/src/components/fantasy/{team-builder,driver-card,budget-meter,league-card,leaderboard}.tsx
```

---

### Task 1: Fantasy rules, budget and scoring (pure)

**Files:**
- Create: `packages/core-py/src/f1_core/fantasy/{__init__,rules,scoring,budget}.py`
- Test: `packages/core-py/tests/fantasy/{test_scoring.py,test_budget.py,test_properties.py}`

**Interfaces:**
- Produces:
  - `ScoringRules(version: int, race_points: tuple[int, ...] (25,18,15,12,10,8,6,4,2,1), qualifying_points: tuple[int, ...] (10,9,...,1), position_gained: int = 1, position_lost: int = -1, fastest_lap: int = 5, dnf: int = -10, dns: int = 0, sprint_points: tuple[int, ...] (8,7,...,1), constructor_both_points_bonus: int = 5, captain_multiplier: int = 2)`.
  - `DriverRaceResult(driver_ref, team_ref, grid: int | None, position: int | None, status: Literal["finished","dnf","dns","dsq"], fastest_lap: bool, quali_position: int | None, sprint_position: int | None)`.
  - `score_driver(r: DriverRaceResult, rules, is_captain: bool) -> int`, `score_constructor(team_ref, results, rules) -> int` (sum of its two drivers' non-captain base scores plus bonus when both finish in the points), `score_team(picks: TeamPicks, results: list[DriverRaceResult], rules) -> ScoreBreakdown(total, by_pick: dict[str, int])`.
  - `Prices(drivers: dict[str, int], constructors: dict[str, int])` (tenths of millions), `validate_team(picks, prices, budget: int = 1000) -> None` raising `TeamError(code, message)` with codes `WRONG_DRIVER_COUNT`, `WRONG_CONSTRUCTOR_COUNT`, `DUPLICATE_PICK`, `OVER_BUDGET`, `CAPTAIN_NOT_IN_TEAM`, `UNKNOWN_DRIVER`, `UNKNOWN_CONSTRUCTOR`.

- [ ] **Step 1: Write the failing tests**

```python
def test_winner_from_pole_scores_race_plus_quali_no_position_change(): ...
def test_position_gain_and_loss_use_grid_vs_finish(): ...
def test_dnf_scores_negative_and_dns_zero(): ...
def test_dsq_scores_zero_race_points_and_no_fastest_lap(): ...
def test_fastest_lap_bonus_only_for_classified_in_top_10(): ...
def test_captain_doubles_driver_total(): ...
def test_constructor_bonus_when_both_cars_score(): ...
def test_sprint_points_added_on_sprint_weekends_only(): ...

@pytest.mark.parametrize("picks,code", [
    (drivers4, "WRONG_DRIVER_COUNT"), (dupe_driver, "DUPLICATE_PICK"),
    (over_budget, "OVER_BUDGET"), (captain_outside, "CAPTAIN_NOT_IN_TEAM"),
    (one_constructor, "WRONG_CONSTRUCTOR_COUNT"), (unknown_driver, "UNKNOWN_DRIVER"),
])
def test_validate_team_errors(picks, code): ...

def test_exactly_at_budget_is_valid(): ...

@given(results=st.lists(driver_results(), min_size=5, max_size=22, unique_by=lambda r: r.driver_ref))
def test_scoring_is_deterministic_and_order_independent(results): ...
@given(results=...)
def test_captain_never_scores_less_than_non_captain_when_total_nonnegative(results): ...
```

- [ ] **Step 2: Run to confirm failure**, then implement

```python
# packages/core-py/src/f1_core/fantasy/scoring.py (core of score_driver)
def score_driver(r: DriverRaceResult, rules: ScoringRules, is_captain: bool) -> int:
    total = 0
    if r.quali_position is not None and r.quali_position <= len(rules.qualifying_points):
        total += rules.qualifying_points[r.quali_position - 1]
    if r.sprint_position is not None and r.sprint_position <= len(rules.sprint_points):
        total += rules.sprint_points[r.sprint_position - 1]
    if r.status == "dns":
        return total * (rules.captain_multiplier if is_captain else 1)
    if r.status == "dsq":
        return 0
    if r.status == "dnf":
        total += rules.dnf
    elif r.position is not None:
        if r.position <= len(rules.race_points):
            total += rules.race_points[r.position - 1]
        if r.grid is not None:
            moved = r.grid - r.position
            total += moved * (rules.position_gained if moved > 0 else -rules.position_lost)
        if r.fastest_lap and r.position <= 10:
            total += rules.fastest_lap
    return total * (rules.captain_multiplier if is_captain else 1)
```

Note the sign convention: `position_lost` is stored negative (`-1`), so for a driver who lost places (`moved < 0`) the expression adds `moved * -position_lost`, which is negative. Add a test `test_losing_three_places_subtracts_three` to pin it.

- [ ] **Step 3: Run to confirm pass (90% coverage) and commit**

Run: `uv run pytest packages/core-py/tests/fantasy --cov=f1_core.fantasy --cov-fail-under=90 -v`
Expected: pass.

```bash
git add -A && git commit -m "feat(core): fantasy scoring rules and team validation"
```

---

### Task 2: Pricing model (pure)

**Files:**
- Create: `packages/core-py/src/f1_core/fantasy/pricing.py`
- Test: `packages/core-py/tests/fantasy/test_pricing.py`

**Interfaces:**
- Produces: `initial_prices(ratings: Ratings, drivers, constructors) -> Prices` mapping rating mu to a price between 50 (5.0M) and 300 (30.0M) drivers, 80 to 300 constructors, rounded to 1 (tenth); `update_prices(prices, recent_points: dict[str, float], rules) -> Prices` moves each price by at most 5 (0.5M) per round, towards a target derived from a rolling average of points, never outside the bounds. Total price of the top 5 drivers and 2 constructors must exceed the 100.0M budget so a full star team is impossible (property test).

- [ ] **Step 1: Write the failing tests** (bounds respected; max move per round 5; unknown or new driver gets a median price; top-heavy team cannot fit the budget; determinism)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(core): fantasy pricing model"
```

---

### Task 3: Schema and team API with lock enforcement

**Files:**
- Create: `packages/db-py/src/f1_db/models/fantasy.py`, `packages/db-py/alembic/versions/0007_fantasy.py`, `apps/api/src/f1_api/{schemas,services,routers}/fantasy_teams.py`
- Test: `packages/db-py/tests/test_schema_phase4.py`, `apps/api/tests/test_fantasy_teams_api.py`

**Interfaces:**
- Tables: `scoring_rules(id, version unique, rules_json, active, created_at)`, `fantasy_prices(id, season_id, round, ref, kind: "driver"|"constructor", price)` unique `(season_id, round, ref, kind)`, `fantasy_teams(id, user_id TEXT (auth user id), season_id, name, captain_ref, created_at)` unique `(user_id, season_id)`, `fantasy_picks(id, team_id, ref, kind)` unique `(team_id, ref, kind)`, `fantasy_pick_history(id, team_id, round, snapshot_json, saved_at)` (a frozen copy taken at lock time), `fantasy_scores(id, team_id, race_id, rules_version, total, breakdown_json, scored_at)` unique `(team_id, race_id, rules_version)`, `leagues`, `league_members` (Task 5).
- Endpoints (auth required):
  - `GET /v1/fantasy/me/team?season=` returns the team and current prices, `locks_at` for the next round, and `locked: bool`.
  - `PUT /v1/fantasy/me/team` body `{season, name (3..30), driver_refs: [5], constructor_refs: [2], captain_ref}`. Validates with `validate_team` against current prices; rejects with `409 {"code": "LOCKED", "locks_at": ...}` when `now() >= locks_at` (qualifying `starts_at` of the next round, from `race_sessions`). Upsert in one transaction with `SELECT ... FOR UPDATE` on the team row so concurrent saves serialise.
  - `GET /v1/fantasy/prices?season=&round=`.
  - A lock-time job `snapshot_picks_at_lock` copies picks into `fantasy_pick_history` for the round (Task 4).

- [ ] **Step 1: Write the failing tests**

```python
async def test_save_valid_team_then_read_back(client, auth_headers): ...
async def test_over_budget_is_422_with_code(client, auth_headers): ...
async def test_edit_after_lock_is_409_with_locks_at(client, auth_headers, freeze_db_time): ...
async def test_save_at_exact_lock_instant_is_rejected(client, auth_headers, freeze_db_time): ...
async def test_concurrent_saves_serialise_and_last_valid_wins(client, auth_headers): ...
async def test_other_users_team_is_not_readable(client, auth_headers, other_headers): ...
async def test_unauthenticated_is_401(client): ...
async def test_unknown_driver_ref_is_422(client, auth_headers): ...
```

`freeze_db_time` sets `race_sessions.starts_at` for the next qualifying to `now() + interval` values rather than patching Python clocks (the database is the clock). `auth_headers` builds JWTs signed with the test RSA key from Phase 0 Task 16 (move that fixture into a shared `apps/api/tests/auth_fixtures.py`).

- [ ] **Step 2: Implement and commit**

Lock check inside the transaction: `select starts_at, now() from race_sessions where type='Q' and race_id=<next race>`; reject when `now() >= starts_at - interval '0 seconds'`.

Run: `uv run pytest packages/db-py apps/api -v && pnpm contract` (Expected: pass.)

```bash
git add -A && git commit -m "feat(api): fantasy team save with database-clock lock enforcement"
```

---

### Task 4: Scoring and lock snapshot jobs

**Files:**
- Create: `apps/worker/src/f1_worker/jobs/{fantasy_scoring,fantasy_pricing}.py`
- Modify: `apps/worker/src/f1_worker/settings.py`
- Test: `apps/worker/tests/test_fantasy_scoring.py`

**Interfaces:**
- Produces:
  - `snapshot_picks_at_lock(session_factory, race_id) -> int` copies every team's picks into `fantasy_pick_history` (idempotent on `(team_id, round)`).
  - `score_race(session_factory, race_id, rules_version: int | None = None) -> int` loads results (`SessionResult` for `R`, `Q`, `SPRINT`), builds `DriverRaceResult` (maps statuses: `Finished`, `+N Laps` to finished; `Did not start` to dns; `Disqualified` to dsq; everything else to dnf; fastest lap flag from lap data when available, else none), scores every team using its `fantasy_pick_history` row (NOT live picks), and writes `fantasy_scores` with `ON CONFLICT (team_id, race_id, rules_version) DO NOTHING`. Skips cancelled races. Returns teams scored. Safe to run concurrently (advisory lock `pg_advisory_xact_lock(hash(race_id))`).
  - Crons: `tick_fantasy` every 5 minutes: snapshot when a Q session has started and no snapshot exists; score when the race is `finished` and results are present and no scores exist for the active version; `update_prices` after scoring.

- [ ] **Step 1: Write the failing tests**

```python
async def test_scores_use_locked_snapshot_not_later_edits(...): ...
async def test_scoring_twice_does_not_duplicate_rows(...): ...
async def test_concurrent_scoring_is_safe(...): ...   # asyncio.gather x5
async def test_dns_and_dsq_statuses_mapped(...): ...
async def test_cancelled_race_is_skipped(...): ...
async def test_rule_change_creates_new_rows_without_touching_old(...): ...
async def test_team_without_snapshot_scores_zero_or_is_skipped_per_policy(...): ...
```

Policy: a team that never saved before lock has no snapshot and is skipped (leaderboards treat missing as 0 points for that round).

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(worker): lock snapshots and idempotent fantasy scoring"
```

---

### Task 5: Leagues

**Files:**
- Create: migration part of `0007_fantasy.py` for `leagues(id, name, owner_user_id, invite_code unique, season_id, created_at, max_members default 50)` and `league_members(league_id, user_id, joined_at)` PK `(league_id, user_id)`; `apps/api/src/f1_api/{schemas,services,routers}/leagues.py`
- Test: `apps/api/tests/test_leagues_api.py`

**Interfaces:**
- Produces (auth required):
  - `POST /v1/fantasy/leagues` body `{name (3..40), season}` returns league with `invite_code` (8 chars from `ABCDEFGHJKMNPQRSTUVWXYZ23456789`, generated with `secrets.choice`, retried on collision). Max 5 leagues owned per user.
  - `POST /v1/fantasy/leagues/join` body `{invite_code}`: idempotent for existing members; uniform `404 {"title": "Invite not found"}` for unknown or malformed codes (no information leak); `409 FULL` when at capacity; rate limited to 10 per minute per user.
  - `GET /v1/fantasy/leagues` lists leagues the user belongs to; `GET /v1/fantasy/leagues/{id}` members only (otherwise 404); `DELETE /v1/fantasy/leagues/{id}/members/{user_id}` owner removes a member or a member leaves themselves (owner cannot leave without transferring or deleting).

- [ ] **Step 1: Write the failing tests** (join twice is 200 both times and one member row; wrong code is 404 identical body to malformed code; full league 409; non-member 404 on detail; owner removal works and removed user loses access; code alphabet property test; leaving as owner is 409; rate limit applies)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(api): fantasy leagues with invite codes"
```

---

### Task 6: Leaderboards (pure ranking and API)

**Files:**
- Create: `packages/core-py/src/f1_core/fantasy/leaderboard.py`, `apps/api/src/f1_api/{schemas,services,routers}/leaderboards.py`
- Test: `packages/core-py/tests/fantasy/test_leaderboard.py`, `apps/api/tests/test_leaderboards_api.py`

**Interfaces:**
- Produces:
  - `rank(entries: list[TeamTotals]) -> list[RankedTeam]` where `TeamTotals(team_id, name, created_at, per_race: dict[int, int])`, sorted by total desc, then race wins (rounds where the team had the round's top score), then best single round, then earliest `created_at`; ties get the same `rank` only when all tiebreaks are equal.
  - `GET /v1/fantasy/leaderboard?season=&scope=global|league:<id>&page=&page_size=` (page_size max 100) returns `{entries: [{rank, team_name, user_display, total, last_round, trend}], me: {...} | null, updated_at}`. Global leaderboard cached 60 s in Redis; league leaderboards only for members.

- [ ] **Step 1: Write the failing tests** (tie broken by wins, then best round, then creation time; identical everything yields equal ranks; empty league returns empty entries; non-member scope gets 404; pagination boundaries; `me` included even when off-page; users appear by display name only, never email)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat: fantasy leaderboards with stable tiebreaks"
```

---

### Task 7: Web: team builder

**Files:**
- Create: `apps/web/src/app/fantasy/team/page.tsx`, `apps/web/src/components/fantasy/{team-builder,driver-card,budget-meter,lock-countdown}.tsx`, `apps/web/src/lib/fantasy-validate.ts`
- Test: `apps/web/src/lib/fantasy-validate.test.ts`, `apps/web/src/components/fantasy/team-builder.test.tsx`

**Interfaces:**
- Produces: `validateTeamClient(selection, prices, budget) -> TeamIssue[]` mirroring server rules for instant feedback; `<BudgetMeter spent budget />` (turns red over budget, announces changes to screen readers with `aria-live="polite"`); `<LockCountdown locksAt />` using the server-provided `locks_at` and the response `Date` header to correct for client clock skew; after lock the builder becomes read-only with a clear banner. Optimistic save with rollback and a toast on `409 LOCKED`.

- [ ] **Step 1: Write the failing tests** (cannot select a sixth driver; deselect restores budget; captain must be a selected driver and clears when that driver is removed; over-budget disables save with explanation; clock skew correction; locked state is read-only; keyboard operable)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(web): fantasy team builder with budget and lock"
```

---

### Task 8: Web: leagues and leaderboards

**Files:**
- Create: `apps/web/src/app/fantasy/{page.tsx,leagues/page.tsx,leagues/[id]/page.tsx}`, `apps/web/src/components/fantasy/{league-card,leaderboard,create-league-dialog,join-league-form}.tsx`
- Test: `apps/web/src/components/fantasy/*.test.tsx`, `apps/web/e2e/fantasy.spec.ts`

**Interfaces:**
- Produces: the leaderboard uses `TimingTowerRow` with rank, team name, total, and a trend arrow (up, down, same) and highlights the signed-in user's row. Invite code is shown with a copy button and share link. The join form normalises input (trim, uppercase, strip spaces and dashes) before sending.

- [ ] **Step 1: Write the failing tests** (invite code normalisation; user's own row highlighted; trend arrows; generic error on bad invite; empty states for no leagues and no scores)

- [ ] **Step 2: Implement, E2E and commit**

`fantasy.spec.ts`: user A signs up, builds a valid team, creates a league; user B signs up in a second browser context, joins by code and builds a team; both see each other on the league leaderboard.

```bash
git add -A && git commit -m "feat(web): fantasy leagues and leaderboards"
```

---

### Task 9: Mock weekend end-to-end, admin tools and parity

**Files:**
- Create: `apps/api/src/f1_api/routers/fantasy_admin.py`, `apps/worker/scripts/mock_weekend.py`, `apps/api/tests/test_fantasy_admin.py`, `docs/parity/phase-4.md`, `docs/runbooks/fantasy-scoring.md`
- Test: `apps/worker/tests/test_mock_weekend.py`

**Interfaces:**
- Produces: admin-only endpoints (role claim `admin` in JWT, otherwise 403): `POST /v1/admin/fantasy/rescore {race_id, rules_version}` (writes new rows, never edits old), `POST /v1/admin/fantasy/rules` (creates a new version, inactive until activated), `POST /v1/admin/fantasy/rules/{version}/activate`. Every admin action is audit-logged to an `admin_audit` table (who, what, when, payload).
- `mock_weekend.py` seeds users, teams, a league, qualifying and race results, runs lock snapshot and scoring, and prints leaderboards. `test_mock_weekend.py` asserts exact expected totals for a hand-computed weekend (3 teams, 8 drivers), including captain, DNF, DNS and sprint cases.

- [ ] **Step 1: Write the failing tests** (non-admin 403; rescoring with a new version leaves old rows untouched; activation switches which version the scoring job uses; audit rows written; mock weekend totals equal hand-computed values)

- [ ] **Step 2: Implement, run the full suite, commit**

Run: `uv run pytest && pnpm test && pnpm --filter @f1/web e2e`
Expected: green. Parity: legacy `Favorites` and persisted selections are handled in Phase 5; fantasy is new, so the parity list notes "no legacy equivalent".

```bash
git add -A && git commit -m "feat(fantasy): admin tools, mock weekend verification and runbook"
```

Open the PR `phase-4-fantasy`. Exit criterion: a mock race weekend scores correctly end to end.
