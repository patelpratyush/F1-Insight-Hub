import os
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from f1_api.config import Settings
from f1_api.main import create_app
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

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


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    with RedisContainer("redis:7-alpine") as r:
        yield f"redis://{r.get_container_host_ip()}:{r.get_exposed_port(6379)}/0"


@pytest.fixture
def settings(pg_url: str, redis_url: str) -> Settings:
    return Settings(
        environment="test",
        database_url=pg_url,
        redis_url=redis_url,
        auth_issuer="http://auth.test",
        auth_jwks_url="http://auth.test/jwks",
        cors_origins=["http://localhost:3000"],
    )


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c,
    ):
        yield c
