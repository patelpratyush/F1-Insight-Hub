from fastapi import APIRouter, Depends, Request, Response

from f1_api.deps import DbSession
from f1_api.errors import ProblemError
from f1_api.http_cache import cached_json
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.teams import TeamProfile
from f1_api.services.teams import TeamService

router = APIRouter(prefix="/v1/teams", tags=["teams"])


@router.get(
    "/{ref}",
    responses={200: {"model": TeamProfile}},
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getTeam",
)
async def team(request: Request, db: DbSession, ref: str) -> Response:
    profile = await TeamService(db).profile(ref)
    if profile is None:
        raise ProblemError(404, "Not found", f"No team {ref!r}")
    return cached_json(request, profile)
