import os
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from f1_db.session import make_engine, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer

DB_DIR = Path(__file__).resolve().parents[3] / "packages" / "db-py"


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        url = pg.get_connection_url()
        subprocess.run(
            ["alembic", "upgrade", "head"],  # noqa: S607
            cwd=DB_DIR,
            check=True,
            env={**os.environ, "DATABASE_URL": url},
        )
        yield url


@pytest.fixture
async def session_factory(pg_url: str) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_engine(pg_url)
    yield make_session_factory(engine)
    await engine.dispose()


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    from testcontainers.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as r:
        yield f"redis://{r.get_container_host_ip()}:{r.get_exposed_port(6379)}/0"
