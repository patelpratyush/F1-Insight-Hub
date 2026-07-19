from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..deps import get_cache
from ..models.common import AppError
from ..services.results import ResultsService

router = APIRouter(tags=["f1"])


def _regulation_era(year: int) -> str:
    """Rough regulation-era label so cross-era stats aren't presented as
    directly comparable (car/aero rules reset in 2022 and again in 2026)."""
    if year >= 2026:
        return "2026+ (new regulations)"
    if year >= 2022:
        return "2022-2025 (ground-effect era)"
    return "pre-2022"


@router.get("/dashboard/{year}")
async def dashboard(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    svc = ResultsService(cache)
    return {
        "year": year,
        "data_year": year,
        "championship_standings": svc.get_driver_standings(year),
        "latest_race": svc.get_latest_race(year),
        "upcoming_race": svc.get_next_race(year),
        "season_statistics": cache.get_season_stats(year),
        "performance_trends": svc.get_performance_trends(year, limit=5),
    }


@router.get("/dashboard-trends/{year}")
async def dashboard_trends(
    year: int,
    all_races: bool = Query(False),
    cache=Depends(get_cache),
):
    await cache.ensure_year(year)
    svc = ResultsService(cache)
    limit = 0 if all_races else 5
    return {
        "year": year,
        "performance_trends": svc.get_performance_trends(year, limit=limit),
    }


@router.get("/driver/{code}")
async def driver_profile(
    code: str,
    years: int = Query(5, ge=1, le=15),
    cache=Depends(get_cache),
):
    current = cache.current_year
    code_upper = code.upper()
    seasons = []
    name = None
    for y in range(current, current - years, -1):
        await cache.ensure_year(y)
        entry = next(
            (s for s in cache.get_driver_standings(y) if s.get("driver") == code_upper),
            None,
        )
        if entry:
            name = entry["name"]
            seasons.append({
                "year": y,
                "position": entry["position"],
                "points": entry["points"],
                "wins": entry["wins"],
                "team": entry["team"],
                "regulation_era": _regulation_era(y),
            })

    if not seasons:
        raise AppError(
            "DRIVER_NOT_FOUND",
            f"No standings found for driver '{code_upper}' in the last {years} seasons",
            status_code=404,
        )

    return {
        "code": code_upper,
        "name": name,
        "current_team": seasons[0]["team"],
        "seasons": seasons,
        "career_totals": {
            "seasons": len(seasons),
            "wins": sum(s["wins"] for s in seasons),
            "points": round(sum(s["points"] for s in seasons), 1),
            "best_position": min(s["position"] for s in seasons),
        },
    }


@router.get("/team/{name}")
async def team_profile(
    name: str,
    years: int = Query(5, ge=1, le=15),
    cache=Depends(get_cache),
):
    current = cache.current_year
    seasons = []
    for y in range(current, current - years, -1):
        await cache.ensure_year(y)
        entry = next(
            (s for s in cache.get_constructor_standings(y) if s.get("team_name", "").lower() == name.lower()),
            None,
        )
        if entry:
            seasons.append({
                "year": y,
                "position": entry["position"],
                "points": entry["points"],
                "wins": entry["wins"],
                "regulation_era": _regulation_era(y),
            })

    if not seasons:
        raise AppError(
            "TEAM_NOT_FOUND",
            f"No standings found for team '{name}' in the last {years} seasons",
            status_code=404,
        )

    return {
        "name": name,
        "seasons": seasons,
        "career_totals": {
            "seasons": len(seasons),
            "wins": sum(s["wins"] for s in seasons),
            "points": round(sum(s["points"] for s in seasons), 1),
            "best_position": min(s["position"] for s in seasons),
        },
    }


@router.get("/compare-seasons")
async def compare_seasons(
    years: str = Query(..., description="Comma-separated years, e.g. 2023,2024,2025"),
    cache=Depends(get_cache),
):
    try:
        year_list = sorted({int(y.strip()) for y in years.split(",") if y.strip()})
    except ValueError:
        raise AppError("INVALID_YEARS", "years must be a comma-separated list of integers", status_code=400)

    if len(year_list) < 2:
        raise AppError("INVALID_YEARS", "provide at least 2 years to compare", status_code=400)

    results = []
    for y in year_list:
        await cache.ensure_year(y)
        results.append({
            "year": y,
            "regulation_era": _regulation_era(y),
            "driver_standings": cache.get_driver_standings(y),
            "constructor_standings": cache.get_constructor_standings(y),
        })

    eras = {r["regulation_era"] for r in results}
    return {
        "years": year_list,
        "seasons": results,
        "spans_regulation_change": len(eras) > 1,
    }
