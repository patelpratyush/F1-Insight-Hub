from fastapi import APIRouter, Depends
from ..models.strategy import (
    StrategyRequest, StrategyCompareRequest, StrategyOptimizeRequest,
)
from ..deps import get_strategy_service

router = APIRouter(tags=["strategy"])


@router.post("/simulate")
async def simulate(body: StrategyRequest, svc=Depends(get_strategy_service)):
    return await svc.simulate(
        body.driver, body.track, body.laps, body.starting_tire, body.weather,
        stint_compounds=body.stint_compounds,
    )


@router.post("/compare")
async def compare(body: StrategyCompareRequest, svc=Depends(get_strategy_service)):
    results = await svc.compare(body.driver, body.track, body.laps, body.strategies, body.weather)
    return {
        "strategies_compared": len(results),
        "results": {r["summary"]: r for r in results},
    }


@router.post("/optimize")
async def optimize(body: StrategyOptimizeRequest, svc=Depends(get_strategy_service)):
    result = await svc.optimize(body.driver, body.track, body.laps, body.weather, body.use_ai)
    best = result["optimal"]
    alternatives = result["alternatives"]
    return {
        "optimal_strategy": best["summary"],
        "predicted_position": best["predicted_position"],
        "total_race_time": best["total_race_time"],
        "total_seconds": best["total_seconds"],
        "efficiency_score": best["efficiency_score"],
        "confidence": best["confidence"],
        "confidence_score": best["confidence"],
        "stints": best["stints"],
        "pit_stops": best["pit_stops"],
        "timeline": best["timeline"],
        "optimization_metrics": best["optimization_metrics"],
        "risk_analysis": best["risk_analysis"],
        "alternative_strategies": [
            {
                "strategy": r["summary"],
                "predicted_position": r["predicted_position"],
                "total_race_time": r["total_race_time"],
                "efficiency_score": r["efficiency_score"],
            }
            for r in alternatives
        ],
        "ai_powered": bool(best.get("ai_insight")),
        "ai_reasoning": best.get("ai_insight"),
    }


@router.get("/tire-compounds/{track}")
async def tire_compounds(track: str, svc=Depends(get_strategy_service)):
    return svc.get_tire_compounds(track)


@router.get("/tracks")
async def available_tracks(svc=Depends(get_strategy_service)):
    return {"tracks": svc.get_available_tracks()}
