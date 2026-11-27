from typing import Annotated

from fastapi import APIRouter, Depends, Query

from f1_api.deps import DbSession
from f1_api.middleware.rate_limit import rate_limit
from f1_api.schemas.search import SearchHit
from f1_api.services.search import SearchService

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.get(
    "",
    response_model=list[SearchHit],
    dependencies=[Depends(rate_limit(60, 60))],
    operation_id="search",
)
async def search(
    db: DbSession, q: Annotated[str, Query(min_length=2, max_length=64)]
) -> list[SearchHit]:
    return await SearchService(db).search(q)
