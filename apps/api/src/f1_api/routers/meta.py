from f1_db.models import IngestionRun
from fastapi import APIRouter
from sqlalchemy import func, select

from f1_api.deps import DbSession
from f1_api.schemas.meta import FreshnessOut

router = APIRouter(prefix="/v1/meta", tags=["meta"])


@router.get("/freshness", response_model=list[FreshnessOut], operation_id="getFreshness")
async def freshness(db: DbSession) -> list[FreshnessOut]:
    jobs = (await db.execute(select(IngestionRun.job).distinct())).scalars().all()
    out: list[FreshnessOut] = []
    for job in jobs:
        last_success = (
            await db.execute(
                select(func.max(IngestionRun.finished_at)).where(
                    IngestionRun.job == job, IngestionRun.status == "success"
                )
            )
        ).scalar()
        last_status = (
            await db.execute(
                select(IngestionRun.status)
                .where(IngestionRun.job == job)
                .order_by(IngestionRun.started_at.desc())
                .limit(1)
            )
        ).scalar_one()
        out.append(FreshnessOut(job=job, last_success_at=last_success, last_status=last_status))
    return out
