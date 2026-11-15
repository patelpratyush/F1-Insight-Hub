import pytest
from f1_db.models import IngestionRun
from f1_worker.runs import record_run
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def test_success_run_recorded(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with record_run(session_factory, "t-success") as run:
        run.rows = 7
    async with session_factory() as s:
        stmt = select(IngestionRun).where(IngestionRun.job == "t-success")
        row = (await s.execute(stmt)).scalar_one()
    assert row.status == "success" and row.rows == 7 and row.finished_at is not None


async def test_failed_run_recorded_and_reraised(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(ValueError, match="bad"):
        async with record_run(session_factory, "t-fail"):
            raise ValueError("bad")
    async with session_factory() as s:
        stmt = select(IngestionRun).where(IngestionRun.job == "t-fail")
        row = (await s.execute(stmt)).scalar_one()
    assert row.status == "failed" and "bad" in (row.error or "")
