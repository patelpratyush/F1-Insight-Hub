import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from f1_db.models import DriverStanding, Season
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed_standings.py"
FIXTURE = Path(__file__).parent / "fixtures" / "driver_standings_2025.json"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("seed_standings", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_seed_from_fixture_needs_no_network(
    session_factory: async_sessionmaker[AsyncSession],
    pg_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with session_factory() as s:
        await s.execute(
            text("truncate driver_standings, drivers, teams, seasons, ingestion_runs cascade")
        )
        await s.commit()
    monkeypatch.setenv("DATABASE_URL", pg_url)
    count = await _load().main(["--fixture", str(FIXTURE)])
    assert count == 2
    async with session_factory() as s:
        year = (await s.execute(select(Season.year))).scalar_one()
        rows = (await s.execute(select(func.count()).select_from(DriverStanding))).scalar_one()
    assert year == 2025
    assert rows == 2
