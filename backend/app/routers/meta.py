from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from ..deps import get_cache

router = APIRouter(tags=["meta"])


def _y(year: Optional[int]) -> int:
    return year or datetime.now(timezone.utc).year


@router.get("/drivers/{year}")
async def drivers(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    return {"year": year, "drivers": cache.get_drivers(year)}


@router.get("/drivers")
async def drivers_current(year: Optional[int] = Query(None), cache=Depends(get_cache)):
    y = _y(year)
    await cache.ensure_year(y)
    return {"year": y, "drivers": cache.get_drivers(y)}


@router.get("/constructors/{year}")
async def constructors(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    return {"year": year, "constructors": cache.get_constructors(year)}


@router.get("/constructors")
async def constructors_current(year: Optional[int] = Query(None), cache=Depends(get_cache)):
    y = _y(year)
    await cache.ensure_year(y)
    return {"year": y, "constructors": cache.get_constructors(y)}


@router.get("/schedule/{year}")
async def schedule(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    return {"year": year, "schedule": cache.get_schedule(year)}


@router.get("/tracks/{year}")
async def tracks(year: int, cache=Depends(get_cache)):
    await cache.ensure_year(year)
    schedule = cache.get_schedule(year)
    return {"year": year, "tracks": [{"name": r["race_name"], "circuit": r["circuit"], "country": r["country"], "date": r["date"]} for r in schedule]}
