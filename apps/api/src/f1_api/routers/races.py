from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response

from f1_api.deps import DbSession, check_season
from f1_api.errors import ProblemError
from f1_api.http_cache import cached_json
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.races import RaceDetail
from f1_api.services.races import RaceService

router = APIRouter(prefix="/v1/races", tags=["races"])


@router.get(
    "/{season}/{round}",
    responses={200: {"model": RaceDetail}},
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getRace",
)
async def race(
    request: Request,
    db: DbSession,
    season: Annotated[int, Path(ge=1950, le=2100)],
    round: Annotated[int, Path(ge=1)],
) -> Response:
    check_season(season)
    detail = await RaceService(db).detail(season, round)
    if detail is None:
        raise ProblemError(404, "Not found", f"No race {season} round {round}")
    return cached_json(request, detail)
