from fastapi import APIRouter, Depends, Request, Response

from f1_api.deps import DbSession, SeasonQuery, check_season, current_year
from f1_api.http_cache import cached_json
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.calendar import RaceSummary
from f1_api.services.calendar import CalendarService

router = APIRouter(prefix="/v1/calendar", tags=["calendar"])


@router.get(
    "",
    responses={200: {"model": list[RaceSummary]}},
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getCalendar",
)
async def calendar(request: Request, db: DbSession, season: SeasonQuery = None) -> Response:
    service = CalendarService(db)
    if season is not None:
        check_season(season)
        return cached_json(request, await service.summaries(season))
    # No season requested: current season, else the latest season that has races.
    rows = await service.summaries(current_year())
    if not rows and (fallback := await service.latest_season_with_races()) is not None:
        rows = await service.summaries(fallback)
    return cached_json(request, rows)
