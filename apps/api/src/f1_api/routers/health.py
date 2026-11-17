from fastapi import APIRouter, Response
from sqlalchemy import text

from f1_api.deps import DbSession, RedisDep

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(db: DbSession, redis: RedisDep, response: Response) -> dict[str, str]:
    result = {"postgres": "ok", "redis": "ok"}
    try:
        await db.execute(text("select 1"))
    except Exception:
        result["postgres"] = "down"
    try:
        await redis.ping()
    except Exception:
        result["redis"] = "down"
    if "down" in result.values():
        response.status_code = 503
    return result
