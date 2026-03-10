from fastapi import Request
from .services.cache import CacheService
from .services.jolpica import JolpicaClient
from .services.prediction import PredictionService


def get_cache(request: Request) -> CacheService:
    return request.app.state.cache


def get_jolpica(request: Request) -> JolpicaClient:
    return request.app.state.jolpica


def get_prediction_service(request: Request) -> PredictionService:
    return PredictionService(cache=request.app.state.cache)
