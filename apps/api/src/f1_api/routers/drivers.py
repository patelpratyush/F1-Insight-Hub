from fastapi import APIRouter, Depends, Request, Response

from f1_api.deps import DbSession
from f1_api.errors import ProblemError
from f1_api.http_cache import cached_json
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.drivers import DriverProfile
from f1_api.services.drivers import DriverService

router = APIRouter(prefix="/v1/drivers", tags=["drivers"])


@router.get(
    "/{ref}",
    responses={200: {"model": DriverProfile}},
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getDriver",
)
async def driver(request: Request, db: DbSession, ref: str) -> Response:
    profile = await DriverService(db).profile(ref)
    if profile is None:
        raise ProblemError(404, "Not found", f"No driver {ref!r}")
    return cached_json(request, profile)
