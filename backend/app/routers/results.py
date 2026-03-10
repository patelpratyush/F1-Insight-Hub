from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from ..deps import get_cache
from ..models.common import AppError
from ..services.results import ResultsService

router = APIRouter(tags=["results"])


def _year(request: Request, year: Optional[int] = None) -> int:
    return year or datetime.now(timezone.utc).year


@router.get("/standings")
async def driver_standings(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    await cache.ensure_year(y)
    svc = ResultsService(cache)
    return {"year": y, "standings": svc.get_driver_standings(y)}


@router.get("/constructor-standings")
async def constructor_standings(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    await cache.ensure_year(y)
    svc = ResultsService(cache)
    return {"year": y, "standings": svc.get_constructor_standings(y)}


@router.get("/calendar")
async def calendar(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    await cache.ensure_year(y)
    svc = ResultsService(cache)
    return {"year": y, "calendar": svc.get_calendar(y)}


@router.get("/next-race")
async def next_race(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    svc = ResultsService(cache)
    race = svc.get_next_race(y)
    if not race:
        raise AppError("NO_NEXT_RACE", f"No upcoming races found for {y}", status_code=404)
    return race


@router.get("/recent")
async def recent_races(
    year: Optional[int] = Query(None),
    limit: int = Query(5, ge=1, le=24),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    svc = ResultsService(cache)
    return {"year": y, "races": svc.get_recent_races(y, limit)}


@router.get("/session/{year}/{round}")
async def session_result(
    year: int,
    round: int,
    cache=Depends(get_cache),
):
    await cache.ensure_year(year)
    svc = ResultsService(cache)
    result = svc.get_session_result(year, round)
    if not result:
        raise AppError("RESULT_NOT_FOUND", f"No result for {year} round {round}", status_code=404)
    return result


@router.get("/upcoming")
async def upcoming_races(
    year: Optional[int] = Query(None),
    request: Request = None,
    cache=Depends(get_cache),
):
    y = _year(request, year)
    svc = ResultsService(cache)
    return {"year": y, "races": svc.get_upcoming_races(y)}
