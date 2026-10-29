# Phase 3: Predictions and Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an honest, reproducible prediction engine (ratings, Monte Carlo race simulation, backtests) and a tyre strategy simulator with AI-written explanations, each with a transparent methodology page.

**Architecture:** All modelling lives in pure `f1_core` modules (`ratings`, `race_sim`, `strategy`, `scoring_metrics`) with seeded RNGs so every result is reproducible. The worker computes `rating_snapshots` after each race and stores immutable `prediction_runs`. A backtest harness replays past seasons walk-forward and gates model changes in CI. The api exposes runs and on-demand strategy simulations (cached by parameter hash). Gemini is used only to explain results, behind an adapter with a deterministic fallback.

**Tech Stack:** numpy, scipy, hypothesis (property tests), Google Gemini via `google-genai`, Phase 0 to 2 stack.

**Spec:** `docs/superpowers/specs/2026-10-29-f1-insight-hub-rewrite-design.md`. Depends on: Phases 0 and 1 (results, calendar, weather). Phase 2 is not required.

## Global Constraints

- Every model has `MODEL_VERSION` (semver string) stored on each run. Changing model code requires bumping it.
- All randomness uses `numpy.random.Generator(PCG64(seed))`. A run's `seed` is stored. Same inputs and seed produce byte-identical output.
- Predictions show probabilities with 95% intervals and never claim accuracy beyond the published backtest metrics.
- Prediction runs are immutable (no UPDATE or DELETE grants in code paths).
- Gemini calls: 10 s timeout, structured output validated with Pydantic, response cached by `sha256(prompt + model)`, hard daily budget from `AI_DAILY_BUDGET_CALLS`, never block a simulation result on the AI call.
- Backtest gate: Brier score for win probability must not worsen by more than 2% relative to the stored baseline, rank correlation must stay above the stored floor.

## Review Focus

1. A rookie or a driver with fewer than 3 races: rating shrinks toward the team mean instead of producing extreme values or division by zero. (Task 1)
2. A wet race or sudden rain forecast: wet-weather factor widens uncertainty and shifts probabilities, and never produces probabilities that do not sum to 1. (Task 3)
3. Fewer than 20 drivers on the grid (reduced field, DNS): simulation and probabilities adapt and still sum to 1. (Task 3)
4. Pit strategy with illegal choices (fewer than two compounds in a dry race, zero stops, pit on lap 0 or after the last lap): rejected with a clear 422 message. (Task 6)
5. Gemini outage, timeout, malformed JSON or budget exhausted: UI shows the simulation with a deterministic summary and no error. (Task 7)
6. A user changes one input slightly: results change smoothly (no wild swings), tested via sensitivity property tests. (Task 3, Task 6)
7. Season start with no prior results: ratings fall back to the previous season's end ratings with inflated uncertainty. (Task 1, Task 2)

---

## File Structure

```
packages/db-py/alembic/versions/0005_predictions.py
packages/db-py/src/f1_db/models/predictions.py
packages/core-py/src/f1_core/ratings/{__init__,elo,priors,features}.py
packages/core-py/src/f1_core/race_sim/{__init__,model,simulate,summary}.py
packages/core-py/src/f1_core/backtest/{__init__,runner,metrics}.py
packages/core-py/src/f1_core/strategy/{__init__,tyres,laptime,simulate,rules,compare}.py
packages/core-py/tests/{ratings,race_sim,backtest,strategy}/...
apps/worker/src/f1_worker/jobs/{ratings,predictions,backtest_job}.py
apps/api/src/f1_api/{schemas,services,routers}/{predictions,strategy,ai}.py
apps/api/src/f1_api/ai/{gemini.py,fallback.py}
apps/web/src/app/{predictions,predictions/[season]/[round],strategy,methodology}/...
baselines/backtest_baseline.json
```

---

### Task 1: Rating engine (pure)

**Files:**
- Create: `packages/core-py/src/f1_core/ratings/{__init__,elo,priors,features}.py`
- Test: `packages/core-py/tests/ratings/{test_elo.py,test_priors.py}`

**Interfaces:**
- Produces:
  - `RaceOutcome(season: int, round: int, finishing: list[Entry])`, `Entry(driver_ref, team_ref, position: int | None, grid: int | None, dnf_reason: Literal["mechanical","accident","other"] | None)`.
  - `Ratings(drivers: dict[str, Rating], teams: dict[str, Rating])` with `Rating(mu: float, sigma: float, races: int)`.
  - `update_ratings(prior: Ratings, outcome: RaceOutcome, params: RatingParams = RatingParams()) -> Ratings`: a team-plus-driver Bradley-Terry/Elo update over all pairwise finishing orders. A driver's performance is `team.mu + driver.mu`. DNFs for mechanical reasons update the team only; accident DNFs update the driver weakly. `sigma` shrinks with races and widens between seasons.
  - `new_season_prior(end: Ratings, params) -> Ratings`: regress means toward the global mean by `params.offseason_regression` (default 0.35) and inflate sigma. Unknown drivers and teams start at `mu=0, sigma=params.sigma_new` and rookies shrink toward their team mean.
  - `win_strength(r: Ratings, driver_ref: str, team_ref: str) -> tuple[float, float]` returning combined `(mu, sigma)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_winner_rating_increases_and_loser_decreases(): ...
def test_update_is_order_independent_within_one_race(): ...  # shuffling entry list gives same ratings
def test_mechanical_dnf_does_not_penalise_driver(): ...
def test_rookie_rating_shrinks_toward_team_mean(): ...
def test_sigma_decreases_with_more_races_and_increases_in_offseason(): ...
def test_new_season_prior_regresses_toward_mean(): ...
def test_empty_or_single_entry_race_is_a_noop(): ...
@given(st.permutations(range(20)))
def test_ratings_mean_is_conserved_across_update(order): ...   # hypothesis: sum of mu changes ~ 0
```

- [ ] **Step 2: Run to confirm failure**, then implement

Core update (full code required in the file):

```python
def update_ratings(prior: Ratings, outcome: RaceOutcome, params: RatingParams = RatingParams()) -> Ratings:
    classified = [e for e in outcome.finishing if e.position is not None]
    if len(classified) < 2:
        return prior
    drivers = {k: replace(v) for k, v in prior.drivers.items()}
    teams = {k: replace(v) for k, v in prior.teams.items()}
    for e in outcome.finishing:
        drivers.setdefault(e.driver_ref, Rating(0.0, params.sigma_new, 0))
        teams.setdefault(e.team_ref, Rating(0.0, params.sigma_new, 0))
    d_delta = defaultdict(float)
    t_delta = defaultdict(float)
    for i, a in enumerate(classified):
        for b in classified[i + 1:]:          # a finished ahead of b
            sa = teams[a.team_ref].mu + drivers[a.driver_ref].mu
            sb = teams[b.team_ref].mu + drivers[b.driver_ref].mu
            p = 1.0 / (1.0 + math.exp(-(sa - sb)))
            g = params.k * (1.0 - p)
            share_team = params.team_share
            t_delta[a.team_ref] += g * share_team;  t_delta[b.team_ref] -= g * share_team
            d_delta[a.driver_ref] += g * (1 - share_team);  d_delta[b.driver_ref] -= g * (1 - share_team)
    n = len(classified) - 1
    for ref, d in d_delta.items():
        drivers[ref] = Rating(drivers[ref].mu + d / n, _shrink(drivers[ref].sigma, params), drivers[ref].races + 1)
    for ref, d in t_delta.items():
        teams[ref] = Rating(teams[ref].mu + d / n, _shrink(teams[ref].sigma, params), teams[ref].races + 1)
    # mechanical DNFs: team only, accident: driver only at half weight (see params)
    return Ratings(drivers=drivers, teams=teams)
```

Add `_shrink(sigma, params) = max(params.sigma_floor, sigma * params.sigma_decay)`, and the DNF handling after the pairwise loop. Defaults: `k=0.9, team_share=0.6, sigma_new=1.0, sigma_floor=0.25, sigma_decay=0.97, offseason_regression=0.35`.

- [ ] **Step 3: Run to confirm pass and commit**

Run: `uv run pytest packages/core-py/tests/ratings -v`
Expected: pass.

```bash
git add -A && git commit -m "feat(core): add team-plus-driver rating engine"
```

---

### Task 2: Ratings snapshots (schema and job)

**Files:**
- Create: `packages/db-py/src/f1_db/models/predictions.py`, `packages/db-py/alembic/versions/0005_predictions.py`, `apps/worker/src/f1_worker/jobs/ratings.py`
- Test: `packages/db-py/tests/test_schema_phase3.py`, `apps/worker/tests/test_ratings_job.py`

**Interfaces:**
- Produces tables `rating_snapshots(id, season_id, after_round, model_version, ratings_json JSONB, created_at)` unique on `(season_id, after_round, model_version)`, `prediction_runs(id, race_id, model_version, seed, inputs_json, output_json, created_at)` (immutable), `backtest_results(id, model_version, season, brier_win, brier_podium, rank_corr, n_races, created_at)`.
- `rebuild_ratings(session_factory, through_season: int) -> int` replays all `SessionResult` rows from 2018 in order, writes one snapshot per race, idempotent. `latest_ratings(session, season, before_round, model_version) -> Ratings` falls back to the previous season's last snapshot passed through `new_season_prior`.

- [ ] **Step 1: Write the failing tests** (rebuild is idempotent; skipping a round does not break chain; first season starts from neutral priors; snapshot JSON round-trips to `Ratings`; `latest_ratings` for round 1 uses prior season with inflated sigma)

- [ ] **Step 2: Implement and commit**

Add DB triggers in the migration that forbid UPDATE and DELETE on `prediction_runs`:

```python
op.execute("""
CREATE FUNCTION forbid_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'prediction_runs is immutable'; END $$ LANGUAGE plpgsql;
CREATE TRIGGER prediction_runs_immutable BEFORE UPDATE OR DELETE ON prediction_runs
FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
""")
```

Test that an UPDATE raises. Run: `uv run pytest packages/db-py apps/worker -v` (Expected: pass.)

```bash
git add -A && git commit -m "feat: rating snapshots, immutable prediction runs and rebuild job"
```

---

### Task 3: Monte Carlo race simulation (pure)

**Files:**
- Create: `packages/core-py/src/f1_core/race_sim/{__init__,model,simulate,summary}.py`
- Test: `packages/core-py/tests/race_sim/{test_simulate.py,test_properties.py}`

**Interfaces:**
- Produces:
  - `RaceContext(grid: dict[str, int], teams: dict[str, str], ratings: Ratings, rain_probability: float, track: TrackProfile, safety_car_rate: float)`, `TrackProfile(overtaking_difficulty: float, power_sensitivity: float, deg_severity: float)`.
  - `simulate_race(ctx: RaceContext, n: int = 10_000, seed: int = 0) -> SimulationResult` where `SimulationResult.finish_matrix: np.ndarray` of shape `(n, drivers)` holding finishing positions, plus `driver_order: list[str]` and `dnf_matrix`.
  - `summarize(result) -> list[DriverPrediction]` with `win_prob, podium_prob, points_prob, expected_position, position_ci95: (int, int), dnf_prob`.
- Model: per-driver latent race pace `= rating mu + noise(sigma_total)` with `sigma_total = sqrt(sigma_rating^2 + sigma_race^2 + (rain * sigma_rain)^2)`, grid advantage scaled by `track.overtaking_difficulty`, DNF probability from team reliability prior (default 6%) plus rain bump, safety car compresses pace gaps (shrinks differences by 40% in simulations where it occurs).

- [ ] **Step 1: Write the failing tests**

```python
def test_win_probabilities_sum_to_one(): ...
def test_podium_probabilities_sum_to_three_over_finishers(): ...  # within 1e-9 when no DNFs
def test_same_seed_is_byte_identical(): np.array_equal(...)
def test_different_seed_differs_but_summaries_close(): ...
def test_stronger_rating_wins_more_often(): ...
def test_pole_sitter_advantage_larger_on_hard_to_overtake_track(): ...
def test_rain_widens_distribution_and_still_sums_to_one(): ...
def test_reduced_field_of_14_works(): ...
def test_single_driver_grid_wins_with_probability_one_or_dnf(): ...
@given(st.floats(0, 1), st.integers(5, 22))
def test_probabilities_valid_for_any_rain_and_field_size(rain, size): ...
def test_sensitivity_small_rating_change_small_probability_change(): ...
```

- [ ] **Step 2: Implement and commit**

Vectorised implementation (no Python loops over simulations):

```python
def simulate_race(ctx: RaceContext, n: int = 10_000, seed: int = 0) -> SimulationResult:
    rng = np.random.Generator(np.random.PCG64(seed))
    drivers = sorted(ctx.grid, key=ctx.grid.get)             # by grid order
    d = len(drivers)
    mu = np.array([win_strength(ctx.ratings, r, ctx.teams[r])[0] for r in drivers])
    sig = np.array([win_strength(ctx.ratings, r, ctx.teams[r])[1] for r in drivers])
    grid_bonus = ctx.track.overtaking_difficulty * GRID_WEIGHT * (d - np.arange(d)) / d
    sigma_total = np.sqrt(sig**2 + SIGMA_RACE**2 + (ctx.rain_probability * SIGMA_RAIN) ** 2)
    pace = mu + grid_bonus + rng.standard_normal((n, d)) * sigma_total
    sc = rng.random(n) < ctx.safety_car_rate
    centered = pace - pace.mean(axis=1, keepdims=True)
    pace = np.where(sc[:, None], pace.mean(axis=1, keepdims=True) + 0.6 * centered, pace)
    p_dnf = np.clip(BASE_DNF + ctx.rain_probability * RAIN_DNF_BUMP, 0, 0.5)
    dnf = rng.random((n, d)) < p_dnf
    key = np.where(dnf, -np.inf, pace)
    order = np.argsort(-key, axis=1, kind="stable")
    finish = np.empty_like(order)
    rows = np.arange(n)[:, None]
    finish[rows, order] = np.arange(1, d + 1)[None, :]
    return SimulationResult(finish_matrix=finish, dnf_matrix=dnf, driver_order=drivers)
```

Constants (`GRID_WEIGHT=0.6, SIGMA_RACE=0.5, SIGMA_RAIN=0.8, BASE_DNF=0.06, RAIN_DNF_BUMP=0.08`) live in `model.py` with documented meaning. `summarize` computes position CI from percentiles 2.5 and 97.5 and ensures win and podium probabilities are computed over all simulations (DNFs count as lost).

Run: `uv run pytest packages/core-py/tests/race_sim -v --hypothesis-seed=0` (Expected: pass.)

```bash
git add -A && git commit -m "feat(core): vectorised monte carlo race simulation"
```

---

### Task 4: Prediction runs (job, API, reproducibility)

**Files:**
- Create: `apps/worker/src/f1_worker/jobs/predictions.py`, `apps/api/src/f1_api/{schemas,services,routers}/predictions.py`
- Test: `apps/worker/tests/test_predictions_job.py`, `apps/api/tests/test_predictions_api.py`

**Interfaces:**
- Produces:
  - `create_prediction_run(session_factory, race_id, *, seed: int | None = None) -> UUID`: builds `RaceContext` from latest ratings, the qualifying grid (or the predicted grid from ratings if qualifying has not happened, flagged `grid_source: "predicted"`), latest weather rain probability, track profile from a seeded table (`f1_core.tracks.TRACK_PROFILES` with a neutral default), runs `simulate_race`, stores `inputs_json` (everything required to rerun) and `output_json`.
  - `replay_run(inputs_json) -> output_json` pure function; test asserts `replay_run(run.inputs_json) == run.output_json`.
  - `GET /v1/predictions/{season}/{round}` returns the latest run: `{model_version, created_at, grid_source, drivers: [DriverPrediction]}`; `GET /v1/predictions/runs/{id}` returns any run by id; `GET /v1/predictions/{season}/{round}/history` lists runs.
  - Worker schedule: create a run on Tuesday after a race for the next race, again after FP3 and after qualifying.

- [ ] **Step 1: Write the failing tests** (replay equality; qualifying missing gives `predicted` grid source; run row cannot be updated (DB trigger); API returns 404 problem when no run; probabilities in response sum to 1 within 1e-6; fractional rain probability from weather rows is used)

- [ ] **Step 2: Implement and commit**

Run: `uv run pytest apps/worker apps/api -v && pnpm contract` (Expected: pass.)

```bash
git add -A && git commit -m "feat: reproducible prediction runs with api"
```

---

### Task 5: Backtest harness and CI gate

**Files:**
- Create: `packages/core-py/src/f1_core/backtest/{__init__,runner,metrics}.py`, `apps/worker/src/f1_worker/jobs/backtest_job.py`, `apps/worker/scripts/run_backtest.py`, `baselines/backtest_baseline.json`, `.github/workflows/backtest.yml`
- Test: `packages/core-py/tests/backtest/{test_metrics.py,test_runner.py}`, `apps/worker/tests/test_backtest_gate.py`

**Interfaces:**
- Produces:
  - Metrics: `brier(probs, outcomes) -> float`, `log_loss(...)`, `spearman(predicted_order, actual_order) -> float`, `calibration_bins(probs, outcomes, bins=10)`.
  - `walk_forward(seasons: list[SeasonData], model: ModelFn, n_sims: int) -> BacktestReport` that for each race uses only data available before it (ratings through previous round, actual qualifying grid, actual weather), simulates, and scores win and podium probabilities, expected-order rank correlation.
  - `check_gate(report, baseline) -> GateResult(ok: bool, reasons: list[str])` enforcing: Brier(win) worsens at most 2% relative, rank correlation at least `baseline.rank_corr_floor`.
  - `run_backtest.py --seasons 2019-2025 --write-baseline` stores results to `backtest_results` and (with the flag) updates `baselines/backtest_baseline.json`.

- [ ] **Step 1: Write the failing tests**

```python
def test_brier_perfect_and_worst(): assert brier([1.0], [1]) == 0.0 and brier([0.0], [1]) == 1.0
def test_spearman_identity_and_reverse(): ...
def test_walk_forward_never_uses_future_data(): ...   # model spy records max round seen per race
def test_gate_fails_when_brier_worsens_over_two_percent(): ...
def test_gate_passes_on_small_noise(): ...
def test_report_includes_calibration_bins_that_sum_to_total(): ...
```

- [ ] **Step 2: Implement, wire CI, commit**

`backtest.yml` runs on PRs touching `packages/core-py/src/f1_core/{ratings,race_sim}/**` or `MODEL_VERSION`: loads a prebuilt fixture dataset (`tests/data/backtest_2019_2025.parquet.zst`, checked in via Git LFS, built once by a script), runs the backtest with `n_sims=2000`, and fails the job if `check_gate` returns not ok. The PR comment shows the metrics table.

Run: `uv run pytest packages/core-py/tests/backtest apps/worker/tests/test_backtest_gate.py -v` (Expected: pass.)

```bash
git add -A && git commit -m "feat: walk-forward backtest with metrics and CI gate"
```

---

### Task 6: Strategy simulator (pure)

**Files:**
- Create: `packages/core-py/src/f1_core/strategy/{__init__,tyres,laptime,rules,simulate,compare}.py`
- Test: `packages/core-py/tests/strategy/{test_rules.py,test_laptime.py,test_simulate.py,test_compare.py}`

**Interfaces:**
- Produces:
  - `Compound = Literal["SOFT","MEDIUM","HARD","INTERMEDIATE","WET"]`, `TyreModel(compound, base_delta_s, deg_per_lap_s, cliff_lap | None)`; `default_tyre_models(track: TrackProfile) -> dict[Compound, TyreModel]`.
  - `Strategy(stints: list[Stint])`, `Stint(compound, laps: int)`; `validate_strategy(s, total_laps, wet: bool) -> None` raising `StrategyError(code, message)` for: zero laps in a stint, sum of laps differs from `total_laps`, fewer than two distinct dry compounds in a dry race, more than 5 stops, a pit on lap 0 or on the last lap.
  - `lap_time(params, compound, tyre_age, fuel_laps_remaining, traffic_penalty) -> float` (fuel burn effect 0.03 s per lap, tyre degradation, optional cliff).
  - `simulate_strategy(params: StrategyParams, strategy: Strategy, n: int, seed: int) -> StrategyOutcome` with per-sim total times including pit loss (`pit_loss_s` default 21), random events (safety car probability with pit-loss reduction of 40% if a stop occurs under SC, VSC, lap-time noise sigma 0.25 s, pit stop time variance 0.4 s).
  - `compare_strategies(params, strategies, n, seed) -> list[StrategyComparison]` with `mean_time_s, p10_s, p90_s, win_prob_vs_best, delta_to_best_s`, sorted by mean time.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("stints,code", [
    ([Stint("SOFT", 0), Stint("HARD", 57)], "EMPTY_STINT"),
    ([Stint("SOFT", 30), Stint("SOFT", 27)], "NEEDS_TWO_COMPOUNDS"),
    ([Stint("SOFT", 30), Stint("HARD", 20)], "LAP_COUNT_MISMATCH"),
    ([Stint("SOFT", 10)] * 7, "TOO_MANY_STOPS"),
])
def test_invalid_strategies_rejected(stints, code): ...

def test_wet_race_allows_single_compound(): ...
def test_softer_tyre_is_faster_when_fresh_but_degrades_faster(): ...
def test_cliff_makes_lap_time_jump_after_cliff_lap(): ...
def test_same_seed_same_outcome(): ...
def test_two_stop_beats_one_stop_when_degradation_is_high(): ...
def test_one_stop_beats_two_stop_when_pit_loss_is_large(): ...
def test_safety_car_reduces_expected_pit_loss(): ...
def test_compare_sorted_by_mean_and_delta_zero_for_best(): ...
@given(st.integers(40, 78))
def test_total_time_is_monotonic_in_laps(total_laps): ...
```

- [ ] **Step 2: Implement and commit**

Total time is computed vectorised over `n` simulations: build per-lap arrays of tyre age and compound per strategy, compute lap time matrix `(n, laps)` with noise, add pit loss at each stint boundary with per-sim SC flags.

Run: `uv run pytest packages/core-py/tests/strategy -v` (Expected: pass.)

```bash
git add -A && git commit -m "feat(core): tyre strategy simulation and comparison"
```

---

### Task 7: AI explanations with fallback

**Files:**
- Create: `apps/api/src/f1_api/ai/{__init__,gemini.py,fallback.py,budget.py}`, `apps/api/src/f1_api/schemas/ai.py`
- Modify: `apps/api/pyproject.toml` (add `google-genai`), `apps/api/src/f1_api/config.py` (`gemini_api_key`, `ai_daily_budget_calls`)
- Test: `apps/api/tests/test_ai.py`

**Interfaces:**
- Produces:
  - `StrategyExplanation(headline: str (<=120 chars), reasons: list[str] (2 to 4), risks: list[str] (1 to 3), recommendation: str)`.
  - `Explainer.explain(comparison: list[StrategyComparison], context: dict) -> tuple[StrategyExplanation, Literal["ai","fallback"]]`. Flow: budget check (Redis `INCR ai:budget:{date}`), cache lookup `ai:expl:{sha256}`, Gemini call with `response_schema=StrategyExplanation`, 10 s timeout; any failure (timeout, 429, invalid JSON, validation error, budget exceeded) returns `fallback.explain(comparison)` which builds the text deterministically from numbers.
  - The prompt contains only numeric results and compound names (no user-provided free text), so prompt injection from users is impossible.

- [ ] **Step 1: Write the failing tests**

```python
async def test_returns_ai_result_and_caches(fake_gemini, redis): ...  # second call does not hit fake_gemini
async def test_timeout_falls_back(fake_gemini_slow): ... source == "fallback"
async def test_invalid_json_falls_back(fake_gemini_bad_json): ...
async def test_budget_exhausted_falls_back_without_calling_gemini(fake_gemini, redis): ...
async def test_fallback_mentions_best_strategy_and_delta(): ...
async def test_prompt_contains_no_user_free_text(): ...
```

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(api): gemini strategy explanations with deterministic fallback"
```

---

### Task 8: Strategy and prediction API

**Files:**
- Create: `apps/api/src/f1_api/{schemas,services,routers}/strategy.py`, migration `0006_strategy.py` (table `strategy_simulations`)
- Test: `apps/api/tests/test_strategy_api.py`

**Interfaces:**
- Produces: `POST /v1/strategy/simulate` body `{season, round | null, total_laps: int (20..80), pit_loss_s: float (10..40), safety_car_probability: float (0..1), wet: bool, strategies: list[{name: str (<=40), stints: list[{compound, laps}]}] (1..6), n: int (500..20000, default 5000), seed: int | null}` returns `{id, params_hash, comparisons: [...], explanation: StrategyExplanation, explanation_source}`. Results cached by `params_hash` (sha256 of canonical JSON, seed included). Validation errors from `validate_strategy` map to `422` problem with `code` and `message` fields. Rate limited to 20 per minute per IP (CPU heavy), and `n` times strategies is capped at 60,000 simulations per request. Simulation runs in a thread pool to avoid blocking the event loop.
- `GET /v1/strategy/simulations/{id}` returns a stored simulation.

- [ ] **Step 1: Write the failing tests** (invalid stint returns 422 with code; identical request returns same id and cached flag; cap exceeded returns 422; explanation falls back when Gemini disabled; concurrent identical requests compute once (Redis lock); response time for 5000 sims, 3 strategies under 1.5 s)

- [ ] **Step 2: Implement and commit**

Run: `uv run pytest apps/api -v && pnpm contract` (Expected: pass.)

```bash
git add -A && git commit -m "feat(api): strategy simulation endpoint with caching and limits"
```

---

### Task 9: Web: predictions pages

**Files:**
- Create: `apps/web/src/app/predictions/page.tsx`, `apps/web/src/app/predictions/[season]/[round]/page.tsx`, `apps/web/src/components/predictions/{probability-bars,position-range,grid-source-badge,prediction-table}.tsx`
- Test: `apps/web/src/components/predictions/*.test.tsx`, `apps/web/e2e/predictions.spec.ts`

**Interfaces:**
- Produces: a timing-tower style prediction table showing win %, podium %, points %, expected position with a range bar (95% interval), DNF %; a badge "Predicted grid" vs "Official grid"; a "Model v{version}, ran {time}" line with a link to `/methodology`; tooltips explaining uncertainty; accessible table with sortable columns.

- [ ] **Step 1: Write the failing tests** (probabilities render with one decimal and sum row is hidden; range bar clamps at grid size; missing run shows "Predictions are published after qualifying" and not an error; 0% and 100% render without NaN)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(web): prediction pages with uncertainty display"
```

---

### Task 10: Web: strategy simulator and methodology

**Files:**
- Create: `apps/web/src/app/strategy/page.tsx`, `apps/web/src/app/methodology/page.tsx`, `apps/web/src/components/strategy/{strategy-builder,compound-picker,result-chart,explanation-card}.tsx`, `apps/web/src/lib/strategy-form.ts`
- Test: `apps/web/src/lib/strategy-form.test.ts`, `apps/web/src/components/strategy/strategy-builder.test.tsx`, `apps/web/e2e/strategy.spec.ts`

**Interfaces:**
- Produces: `validateStrategyForm(values, totalLaps, wet) -> FormErrors` mirroring the backend rules for instant feedback (the server remains the authority). The builder is a drag-to-resize stint bar per strategy (keyboard accessible: arrow keys move a boundary by one lap). Results show a mean-time bar chart with p10 to p90 whiskers, delta to best, win probability, and an explanation card labelled "AI-generated" or "Auto-generated summary" by `explanation_source`. The methodology page documents the rating model, simulation, uncertainty, the backtest metrics table pulled from `/v1/predictions/backtests`, and honest limitations.

- [ ] **Step 1: Write the failing tests** (form validator parity cases; boundary drag cannot make a stint zero laps; loading and error states; explanation label by source)

- [ ] **Step 2: Implement, E2E, commit**

`strategy.spec.ts`: build a one-stop and a two-stop, run, assert results render in under 3 s, assert an invalid single-compound dry strategy shows a field-level error without calling the API.

```bash
git add -A && git commit -m "feat(web): strategy simulator and methodology page"
```

---

### Task 11: Phase 3 hardening and parity

**Files:**
- Create: `docs/parity/phase-3.md`, `docs/runbooks/model-release.md`, `apps/api/tests/load/strategy_simulate.py`

- [ ] **Step 1: Load check** : 50 concurrent simulate calls complete with p95 under 4 s and the api stays responsive (`/healthz` p95 under 50 ms during load).

- [ ] **Step 2: Model release runbook** : bump `MODEL_VERSION`, run backtest locally, update baseline only with PR approval, deploy, rerun rating rebuild, and how old runs remain reproducible with `replay_run` against stored inputs.

- [ ] **Step 3: Parity** : legacy driver predictor, race predictor, full grid prediction, strategy simulator with AI, multi-strategy comparison, weather-driven tyre advice (rain factor and wet rules) all mapped to new tasks. Legacy "accuracy" claim replaced by published backtest metrics.

Run: `uv run pytest && pnpm test && pnpm --filter @f1/web e2e`
Expected: green.

```bash
git add -A && git commit -m "test(predict): load check, release runbook and parity"
```

Open the PR `phase-3-predict-strategy`. Exit criterion: backtest report published and every prediction reproducible by model version.
