from fastapi import APIRouter, Depends, Request
from ..models.predict import (
    DriverPredictRequest, DriverPrediction,
    RacePredictRequest, RaceGridPrediction,
)
from ..models.common import AppError
from ..deps import get_prediction_service

router = APIRouter(tags=["prediction"])


@router.post("/driver", response_model=DriverPrediction)
async def predict_driver(
    body: DriverPredictRequest,
    svc=Depends(get_prediction_service),
):
    result = await svc.predict_driver(body.driver, body.track, body.weather, body.year)
    if not result:
        raise AppError("DRIVER_NOT_FOUND", f"Driver '{body.driver}' not found", status_code=404)
    return result


@router.post("/race", response_model=RaceGridPrediction)
async def predict_race(
    body: RacePredictRequest,
    request: Request,
    svc=Depends(get_prediction_service),
):
    from datetime import datetime, timezone
    year = body.year or datetime.now(timezone.utc).year
    grid = await svc.predict_race_grid(body.track, body.weather, body.year)
    return RaceGridPrediction(
        track=body.track,
        weather=body.weather,
        year=year,
        grid=grid,
    )
