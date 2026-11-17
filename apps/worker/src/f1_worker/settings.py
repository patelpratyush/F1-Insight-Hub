from datetime import UTC, datetime
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings
from arq.cron import CronJob
from f1_db.session import make_engine, make_session_factory
from pydantic_settings import BaseSettings, SettingsConfigDict

from f1_worker.jobs.standings import ingest_driver_standings
from f1_worker.sources.jolpica import JolpicaClient


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://f1:f1@localhost:5432/f1"
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"
    sentry_dsn: str = ""


async def standings_task(ctx: dict[str, Any]) -> int:
    year = datetime.now(UTC).year
    return await ingest_driver_standings(ctx["session_factory"], ctx["jolpica"], year)


async def on_startup(ctx: dict[str, Any]) -> None:
    cfg = Config()
    if cfg.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=cfg.sentry_dsn,
            environment=cfg.environment,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
    ctx["engine"] = make_engine(cfg.database_url)
    ctx["session_factory"] = make_session_factory(ctx["engine"])
    ctx["jolpica"] = JolpicaClient()


async def on_shutdown(ctx: dict[str, Any]) -> None:
    await ctx["jolpica"].client.aclose()
    await ctx["engine"].dispose()


class WorkerSettings:
    functions: ClassVar[list[Any]] = [standings_task]
    cron_jobs: ClassVar[list[CronJob]] = [
        cron(standings_task, minute={0, 30}, unique=True, run_at_startup=True)
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(Config().redis_url)
    max_tries = 3
    job_timeout = 120
