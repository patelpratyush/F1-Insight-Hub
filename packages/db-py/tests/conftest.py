import os
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from f1_db.session import make_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.postgres import PostgresContainer

DB_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        url = pg.get_connection_url()
        env = {**os.environ, "DATABASE_URL": url}
        subprocess.run(["alembic", "upgrade", "head"], cwd=DB_DIR, env=env, check=True)  # noqa: S607
        yield url


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    eng = make_engine(database_url)
    yield eng
    await eng.dispose()
