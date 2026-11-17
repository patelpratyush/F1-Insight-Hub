from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from f1_api.deps import DbSession
from f1_api.errors import ProblemError
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.standings import DriverStandingOut
from f1_api.services.standings import StandingsService

router = APIRouter(prefix="/v1/standings", tags=["standings"])


def _max_year() -> int:
    return datetime.now(UTC).year + 1


@router.get(
    "/drivers",
    response_model=list[DriverStandingOut],
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getDriverStandings",
)
async def driver_standings(
    db: DbSession,
    season: Annotated[int | None, Query(ge=1950, le=2100)] = None,
) -> list[DriverStandingOut]:
    service = StandingsService(db)
    if season is not None:
        if season > _max_year():
            raise ProblemError(422, "Validation error", "season is in the far future")
        return await service.latest_driver_standings(season)
    # No season requested: current season, or the latest season that has data
    # (e.g. before round 1 of a new season). Each row carries its `season`.
    rows = await service.latest_driver_standings(datetime.now(UTC).year)
    if rows:
        return rows
    fallback = await service.latest_season_with_data()
    return await service.latest_driver_standings(fallback) if fallback is not None else []
