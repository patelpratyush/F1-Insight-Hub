#!/usr/bin/env python3
"""
Metadata API routes - dynamic driver, track, schedule, and constructor data.
Replaces hardcoded frontend data files (drivers2025.ts, tracks2025.ts).
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import logging

from services.cache_manager import cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metadata", tags=["Metadata"])


@router.get("/drivers/{year}")
async def get_drivers(year: int):
    """Dynamic driver list with team info for a season.
    Merges driver data with standings to include team assignments.
    Falls back to previous year's standings if current year has none.
    """
    await cache_manager.ensure_year_loaded(year)
    drivers = cache_manager.get_drivers(year)
    if not drivers:
        raise HTTPException(404, f"No driver data for {year}")

    standings = cache_manager.get_driver_standings(year)
    if not standings:
        prev = year - 1
        await cache_manager.ensure_year_loaded(prev)
        standings = cache_manager.get_driver_standings(prev)

    team_map = {}
    for s in (standings or []):
        team_map[s.get("driver", "")] = s.get("team", "")

    enriched = []
    for d in drivers:
        code = d.get("code", "")
        enriched.append({
            **d,
            "team": team_map.get(code, ""),
        })

    return {"success": True, "year": year, "drivers": enriched}


@router.get("/tracks/{year}")
async def get_tracks(year: int):
    """Season schedule with circuit info."""
    await cache_manager.ensure_year_loaded(year)
    schedule = cache_manager.get_schedule(year)
    if not schedule:
        prev = year - 1
        await cache_manager.ensure_year_loaded(prev)
        schedule = cache_manager.get_schedule(prev)
    if not schedule:
        raise HTTPException(404, f"No schedule data for {year}")
    return {"success": True, "year": year, "tracks": schedule}


@router.get("/schedule/{year}")
async def get_schedule(year: int):
    """Full race calendar with completed/upcoming status."""
    await cache_manager.ensure_year_loaded(year)
    schedule = cache_manager.get_schedule(year)
    if not schedule:
        raise HTTPException(404, f"No schedule data for {year}")

    now = datetime.now(timezone.utc).date()
    annotated = []
    for race in schedule:
        entry = dict(race)
        try:
            race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
            entry["status"] = "completed" if race_date < now else "upcoming"
        except (KeyError, ValueError):
            entry["status"] = "unknown"
        annotated.append(entry)

    return {
        "success": True,
        "year": year,
        "total_rounds": len(annotated),
        "schedule": annotated,
    }


@router.get("/constructors/{year}")
async def get_constructors(year: int):
    """Constructor/team list for a season."""
    await cache_manager.ensure_year_loaded(year)
    constructors = cache_manager.get_constructors(year)
    if not constructors:
        raise HTTPException(404, f"No constructor data for {year}")
    return {"success": True, "year": year, "constructors": constructors}
