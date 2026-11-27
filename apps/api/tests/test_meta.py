from datetime import UTC, datetime, timedelta

from f1_db.models import IngestionRun
from f1_db.session import make_engine, make_session_factory
from httpx import AsyncClient
from sqlalchemy import text


async def test_freshness_reports_last_success_per_job(client: AsyncClient, pg_url: str) -> None:
    engine = make_engine(pg_url)
    now = datetime.now(UTC)
    async with make_session_factory(engine)() as s:
        await s.execute(text("truncate ingestion_runs"))
        s.add_all(
            [
                IngestionRun(
                    job="standings",
                    started_at=now - timedelta(hours=2),
                    finished_at=now - timedelta(hours=2),
                    status="success",
                    rows=20,
                ),
                IngestionRun(
                    job="standings",
                    started_at=now,
                    finished_at=now,
                    status="failed",
                    rows=0,
                    error="boom",
                ),
            ]
        )
        await s.commit()
    await engine.dispose()

    rows = (await client.get("/v1/meta/freshness")).json()
    entry = next(r for r in rows if r["job"] == "standings")
    assert entry["last_status"] == "failed"
    assert entry["last_success_at"] is not None
