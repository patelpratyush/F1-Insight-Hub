from fastapi import APIRouter, Depends, Request, Response

from f1_api.deps import DbSession, SeasonQuery, check_season, current_year
from f1_api.http_cache import cached_json
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.standings import ConstructorStandingOut, DriverStandingOut
from f1_api.services.standings import StandingsService

router = APIRouter(prefix="/v1/standings", tags=["standings"])


@router.get(
    "/drivers",
    response_model=list[DriverStandingOut],
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getDriverStandings",
)
async def driver_standings(
    db: DbSession,
    season: SeasonQuery = None,
) -> list[DriverStandingOut]:
    service = StandingsService(db)
    if season is not None:
        check_season(season)
        return await service.latest_driver_standings(season)
    # No season requested: current season, or the latest season that has data
    # (e.g. before round 1 of a new season). Each row carries its `season`.
    rows = await service.latest_driver_standings(current_year())
    if rows:
        return rows
    fallback = await service.latest_season_with_data()
    return await service.latest_driver_standings(fallback) if fallback is not None else []


@router.get(
    "/constructors",
    responses={200: {"model": list[ConstructorStandingOut]}},
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getConstructorStandings",
)
async def constructor_standings(
    request: Request, db: DbSession, season: SeasonQuery = None
) -> Response:
    service = StandingsService(db)
    if season is not None:
        check_season(season)
        return cached_json(request, await service.latest_constructor_standings(season))
    rows = await service.latest_constructor_standings(current_year())
    if not rows and (fallback := await service.latest_season_with_constructor_data()) is not None:
        rows = await service.latest_constructor_standings(fallback)
    return cached_json(request, rows)
