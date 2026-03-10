from fastapi import Request
from .config import settings
from .services.cache import CacheService
from .services.jolpica import JolpicaClient
from .services.prediction import PredictionService
from .services.telemetry import TelemetryService
from .services.strategy import StrategyService
from .services.weather import WeatherService


def get_cache(request: Request) -> CacheService:
    return request.app.state.cache


def get_jolpica(request: Request) -> JolpicaClient:
    return request.app.state.jolpica


def get_prediction_service(request: Request) -> PredictionService:
    return PredictionService(cache=request.app.state.cache)


def get_telemetry_service(request: Request) -> TelemetryService:
    return TelemetryService(cache_dir=settings.resolved_fastf1_dir())


def get_strategy_service(request: Request) -> StrategyService:
    return StrategyService()


def get_weather_service(request: Request) -> WeatherService:
    return WeatherService(
        api_key=settings.openweather_api_key,
        session=request.app.state.jolpica._session,  # reuse shared aiohttp session
    )
