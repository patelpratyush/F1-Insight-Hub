from fastapi import APIRouter, Depends, Request
from ..models.telemetry import (
    TelemetryRequest, DriverComparisonRequest,
    SpeedTraceRequest, TrackMapRequest, WeatherContextRequest,
)
from ..models.common import AppError
from ..deps import get_telemetry_service

router = APIRouter(tags=["telemetry"])


@router.post("/analyze")
async def analyze(body: TelemetryRequest, svc=Depends(get_telemetry_service)):
    result = await svc.analyze(body.year, body.race, body.session, body.driver)
    if "error" in result:
        raise AppError("TELEMETRY_ERROR", result["error"], status_code=404)
    return result


@router.post("/speed-trace")
async def speed_trace(body: SpeedTraceRequest, svc=Depends(get_telemetry_service)):
    result = await svc.speed_trace(body.year, body.race, body.session, body.driver, body.lap)
    if "error" in result:
        raise AppError("TELEMETRY_ERROR", result["error"], status_code=404)
    return result


@router.post("/driver-comparison")
async def driver_comparison(body: DriverComparisonRequest, svc=Depends(get_telemetry_service)):
    result = await svc.driver_comparison(body.year, body.race, body.session, body.driver1, body.driver2)
    return result


@router.post("/track-map")
async def track_map(body: TrackMapRequest, svc=Depends(get_telemetry_service)):
    result = await svc.track_map(body.year, body.race, body.session, body.driver, body.lap)
    if "error" in result:
        raise AppError("TELEMETRY_ERROR", result["error"], status_code=404)
    return result


@router.post("/weather-context")
async def weather_context(body: WeatherContextRequest, svc=Depends(get_telemetry_service)):
    result = await svc.weather_context(body.year, body.race, body.session)
    return result


@router.get("/sessions/{year}")
async def available_sessions(year: int, svc=Depends(get_telemetry_service)):
    return {"year": year, "sessions": await svc.available_sessions(year)}
