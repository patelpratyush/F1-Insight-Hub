from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import structlog
from f1_db.base import utcnow
from f1_db.models import IngestionRun
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class RunHandle:
    rows: int = 0


@asynccontextmanager
async def record_run(
    session_factory: async_sessionmaker[AsyncSession], job: str
) -> AsyncIterator[RunHandle]:
    handle = RunHandle()
    run = IngestionRun(job=job, status="running")
    async with session_factory() as s:
        s.add(run)
        await s.commit()
        run_id = run.id
    log = structlog.get_logger()
    log.info("job_started", job=job)
    try:
        yield handle
    except Exception as exc:
        async with session_factory() as s:
            row = await s.get(IngestionRun, run_id)
            assert row is not None
            row.status, row.finished_at, row.error = "failed", utcnow(), str(exc)[:2000]
            await s.commit()
        log.info("job_finished", job=job, status="failed", error=str(exc)[:200])
        raise
    async with session_factory() as s:
        row = await s.get(IngestionRun, run_id)
        assert row is not None
        row.status, row.finished_at, row.rows = "success", utcnow(), handle.rows
        await s.commit()
    log.info("job_finished", job=job, status="success", rows=handle.rows)
