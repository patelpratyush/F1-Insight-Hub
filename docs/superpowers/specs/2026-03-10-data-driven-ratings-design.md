# Data-Driven Driver & Team Ratings Engine

**Date:** 2026-03-10
**Status:** Approved

## Problem

Current driver and team ratings in `fallback_driver_ratings.json` and `fallback_team_ratings.json` are hand-authored static values. They don't update from real race results, and they don't account for the 2026 regulation reset which invalidates 2025 team order.

## Goal

Replace static ratings with values computed from actual race results:
- **Driver ratings** — derived from 2025 full season (24 races), teammate-normalized to remove car effect
- **Team ratings** — derived from 2026 completed races only (recency-weighted), since new regs reset car competitiveness
- **Confidence blending** — computed ratings blend with hand-authored prior, with computed weight growing as 2026 data accumulates

---

## Architecture

```
CacheService.initialize()
    └── ensure_year(2025)   ← load full 2025 results
    └── ensure_year(2026)   ← load 2026 results (already happens)
    └── RatingsEngine.recompute(cache)
            ├── compute_driver_ratings()   ← 2025 teammate-normalized
            ├── compute_team_ratings()     ← 2026 recency-weighted
            ├── blend_with_prior()         ← confidence = f(n_2026_races)
            └── write → config/computed_ratings.json

CacheService._periodic_refresh()   (every 30 min)
    └── RatingsEngine.recompute(cache)   ← picks up new race results automatically

f1_ratings.compute_driver_scores()
    └── reads computed_ratings.json first, falls back to fallback_*.json
```

### Files

| Action | File |
|--------|------|
| Create | `backend/app/core/ratings_engine.py` |
| Create (runtime) | `backend/config/computed_ratings.json` |
| Modify | `backend/app/services/cache.py` |
| Modify | `backend/app/core/f1_ratings.py` |

**No new API calls needed.** The `grid` field already present in Jolpica race results serves as a qualifying proxy. Everything runs off data already being fetched.

---

## Driver Rating Formula (2025 teammate-normalized)

For each driver, iterate all 2025 races where they and their teammate both participated.

**Grid delta (qualifying proxy):**
```
grid_delta = teammate_grid - driver_grid   (positive = driver qualified ahead)
```
Averaged across all 2025 races. Excludes DNS entries.

**Race delta:**
```
race_delta = teammate_finish - driver_finish   (positive = driver finished ahead)
```
Only counted when both drivers are classified `"Finished"`. DNFs (mechanical, collision) are excluded entirely — they do not penalize the driver.

**Skill score:**
```
raw_skill = 0.5 × normalized(grid_delta) + 0.5 × normalized(race_delta)
```
Both deltas are normalized across the full grid so a midfield driver scores ~0.70 (the existing default). Scaled to realistic F1 range `[0.60, 0.98]`.

**Sub-ratings:**
- `overall_skill` = combined raw_skill
- `wet_skill` = same formula restricted to known wet races; falls back to `overall_skill × 0.97` if fewer than 3 wet races in sample
- `race_craft` = race delta score component
- `strategy_execution` = average of grid and race components

---

## Team Rating Formula (2026 recency-weighted)

Uses only completed 2026 races. Recency weight for race `i` of `N` total:
```
weight[i] = i / sum(1..N)
```
Most recent race always has highest weight, handling mid-season car development.

**Per-race, per-team metrics:**
- `race_score` = recency-weighted average finishing position of classified finishers (DNFs excluded)
- `grid_score` = recency-weighted average grid position of both drivers

**Team ratings:**
```
dry_pace    = 0.6 × normalized(grid_score) + 0.4 × normalized(race_score)
wet_pace    = dry_pace × wet_modifier   (from known wet races)
strategy    = normalized(race_score - grid_score)   # positions gained race vs grid
reliability = classified_finishes / total_starts
```

All scores normalized across all teams to `[0.60, 0.97]`. The team leading 2026 is the ceiling; last place is the floor.

---

## Confidence Blending

Computed ratings blend with the hand-authored prior. The blend weight grows with data volume:

```
confidence = n_2026_races / (n_2026_races + 4)

final_rating = confidence × computed + (1 - confidence) × prior
```

The `+ 4` represents 4 virtual races of trust in the prior.

| 2026 races | confidence | computed | prior |
|-----------|-----------|---------|-------|
| 1 | 0.20 | 20% | 80% |
| 4 | 0.50 | 50% | 50% |
| 8 | 0.67 | 67% | 33% |
| 16 | 0.80 | 80% | 20% |
| 24 | 0.86 | 86% | 14% |

Applied separately to driver ratings and team ratings. The prior (hand-authored JSON) never fully disappears, preventing wild swings from anomalous results.

---

## Output Format

`backend/config/computed_ratings.json`:
```json
{
  "_meta": {
    "generated_at": "2026-03-10T12:00:00Z",
    "n_2025_races": 24,
    "n_2026_races": 1,
    "confidence": 0.20,
    "method": "teammate-normalized 2025 + recency-weighted 2026"
  },
  "drivers": {
    "Max Verstappen": {
      "overall_skill": 0.93,
      "wet_skill": 0.94,
      "race_craft": 0.92,
      "strategy_execution": 0.90
    }
  },
  "teams": {
    "McLaren": {
      "dry_pace": 0.91,
      "wet_pace": 0.88,
      "strategy": 0.85,
      "reliability": 0.92
    }
  }
}
```

---

## Edge Cases

- **Driver with no teammate overlap** (mid-season replacement): use available races only; if fewer than 3, fall back to prior entirely
- **Team with only 1 driver finishing** in a 2026 race: use that driver's result; don't penalize team for teammate DNF
- **All DNFs in a race** (red flag, etc.): exclude that race from team ratings computation
- **2025 data unavailable** (API down at startup): skip driver rating computation, use prior for drivers, still compute team ratings from 2026 data
- **No 2026 races yet**: `confidence = 0`, use prior entirely — identical to current behavior
