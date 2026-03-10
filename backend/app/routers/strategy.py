from fastapi import APIRouter, Depends
from ..models.strategy import (
    StrategyRequest, StrategyCompareRequest, StrategyOptimizeRequest,
)
from ..deps import get_strategy_service

router = APIRouter(tags=["strategy"])


@router.post("/simulate")
async def simulate(body: StrategyRequest, svc=Depends(get_strategy_service)):
    return await svc.simulate(body.driver, body.track, body.laps, body.starting_tire, body.weather)


@router.post("/compare")
async def compare(body: StrategyCompareRequest, svc=Depends(get_strategy_service)):
    return await svc.compare(body.driver, body.track, body.laps, body.strategies, body.weather)


@router.post("/optimize")
async def optimize(body: StrategyOptimizeRequest, svc=Depends(get_strategy_service)):
    return await svc.optimize(body.driver, body.track, body.laps, body.weather, body.use_ai)


@router.get("/tire-compounds/{track}")
async def tire_compounds(track: str, svc=Depends(get_strategy_service)):
    return svc.get_tire_compounds(track)


@router.get("/tracks")
async def available_tracks(svc=Depends(get_strategy_service)):
    return {"tracks": svc.get_available_tracks()}
