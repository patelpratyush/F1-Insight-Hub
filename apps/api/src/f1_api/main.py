from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from f1_db.session import make_engine, make_session_factory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from f1_api.config import Settings, get_settings
from f1_api.errors import install_error_handlers
from f1_api.middleware.request_id import RequestIdMiddleware
from f1_api.routers import health, standings


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(cfg.database_url)
        app.state.engine = engine
        app.state.session_factory = make_session_factory(engine)
        app.state.redis = Redis.from_url(cfg.redis_url, decode_responses=True)
        app.state.settings = cfg
        try:
            yield
        finally:
            await app.state.redis.aclose()
            await engine.dispose()

    app = FastAPI(title="F1 Insight Hub API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(standings.router)
    return app
