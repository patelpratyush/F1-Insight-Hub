import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models.common import AppError, ErrorResponse, HealthResponse
from .services.cache import CacheService
from .services.jolpica import JolpicaClient

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──────────────────────────────────────────────────
    jolpica = JolpicaClient(base_url=settings.jolpica_base)
    await jolpica.open()
    app.state.jolpica = jolpica

    cache = CacheService(
        db_path=settings.resolved_cache_db(),
        jolpica=jolpica,
    )
    await cache.open()
    await cache.initialize()
    app.state.cache = cache

    logger.info("F1 backend ready")
    yield

    # ── shutdown ─────────────────────────────────────────────────
    await cache.close()
    await jolpica.close()
    logger.info("F1 backend shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="F1 Insight Hub API",
        version="4.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.error,
                message=exc.message,
                detail=exc.detail,
            ).model_dump(),
        )

    @app.get("/health", response_model=HealthResponse)
    async def health(request: Request):
        cache: CacheService = request.app.state.cache
        return HealthResponse(
            status="ok",
            cache_initialized=cache.is_initialized,
            year=cache.current_year,
        )

    # Routers registered in Task 6–11
    from .routers import meta, predict, results, telemetry, strategy, weather
    app.include_router(meta.router, prefix="/api/meta")
    app.include_router(predict.router, prefix="/api/predict")
    app.include_router(results.router, prefix="/api/results")
    app.include_router(telemetry.router, prefix="/api/telemetry")
    app.include_router(strategy.router, prefix="/api/strategy")
    app.include_router(weather.router, prefix="/api/weather")

    return app


app = create_app()
