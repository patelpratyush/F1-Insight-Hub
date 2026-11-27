from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.errors import ProblemError


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


DbSession = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]

SeasonQuery = Annotated[int | None, Query(ge=1950, le=2100)]


def check_season(season: int) -> None:
    if season > datetime.now(UTC).year + 1:
        raise ProblemError(422, "Validation error", "season is in the far future")


def current_year() -> int:
    return datetime.now(UTC).year
