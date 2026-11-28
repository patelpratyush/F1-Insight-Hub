from datetime import UTC, datetime
from typing import Any, ClassVar

from arq import cron, func
from arq.connections import RedisSettings
from arq.cron import CronJob
from f1_db.session import make_engine, make_session_factory
from pydantic_settings import BaseSettings, SettingsConfigDict

from f1_worker.jobs.calendar import ingest_calendar
from f1_worker.jobs.constructors import ingest_constructor_standings
from f1_worker.jobs.live_flush import flush_live_session
from f1_worker.jobs.live_poll import poll_live_session
from f1_worker.jobs.results import ingest_results
from f1_worker.jobs.standings import ingest_driver_standings
from f1_worker.jobs.weather import ingest_weather
from f1_worker.scheduling import races_needing_weather, rounds_needing_results, tick_sessions
from f1_worker.sources.jolpica import JolpicaClient
from f1_worker.sources.openf1 import OpenF1Client
from f1_worker.sources.openmeteo import OpenMeteoClient


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://f1:f1@localhost:5432/f1"
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"
    sentry_dsn: str = ""
    # OpenF1 free tier allows 30 requests/min; one poll hits 7 endpoints.
    openf1_poll_seconds: float = 15.0


async def standings_task(ctx: dict[str, Any]) -> int:
    year = datetime.now(UTC).year
    return await ingest_driver_standings(ctx["session_factory"], ctx["jolpica"], year)


async def calendar_task(ctx: dict[str, Any]) -> int:
    return await ingest_calendar(ctx["session_factory"], ctx["jolpica"], datetime.now(UTC).year)


async def constructors_task(ctx: dict[str, Any]) -> int:
    year = datetime.now(UTC).year
    return await ingest_constructor_standings(ctx["session_factory"], ctx["jolpica"], year)


async def results_task(ctx: dict[str, Any]) -> int:
    year = datetime.now(UTC).year
    total = 0
    for rnd in await rounds_needing_results(ctx["session_factory"], year):
        total += await ingest_results(ctx["session_factory"], ctx["jolpica"], year, rnd)
    return total


async def weather_task(ctx: dict[str, Any]) -> int:
    total = 0
    for race_id in await races_needing_weather(ctx["session_factory"], datetime.now(UTC).date()):
        total += await ingest_weather(ctx["session_factory"], ctx["openmeteo"], race_id)
    return total


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
    ctx["openf1"] = OpenF1Client()
    ctx["openmeteo"] = OpenMeteoClient()
    ctx["openf1_poll_seconds"] = cfg.openf1_poll_seconds


async def on_shutdown(ctx: dict[str, Any]) -> None:
    await ctx["jolpica"].client.aclose()
    await ctx["openf1"].client.aclose()
    await ctx["openmeteo"].client.aclose()
    await ctx["engine"].dispose()


class WorkerSettings:
    functions: ClassVar[list[Any]] = [
        standings_task,
        # A live poll runs for the whole session; the default 120 s timeout would kill it.
        func(poll_live_session, timeout=4 * 3600, max_tries=1),
        flush_live_session,
    ]
    cron_jobs: ClassVar[list[CronJob]] = [
        cron(standings_task, minute={0, 30}, unique=True, run_at_startup=True),
        cron(tick_sessions, unique=True),  # every minute
        cron(calendar_task, hour={3}, minute={0}, unique=True, run_at_startup=True),
        cron(constructors_task, minute={10}, unique=True),
        cron(results_task, minute={20}, unique=True),
        cron(weather_task, hour={0, 3, 6, 9, 12, 15, 18, 21}, minute={40}, unique=True),
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(Config().redis_url)
    max_tries = 3
    job_timeout = 120
