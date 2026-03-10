from fastapi import APIRouter, Depends, Request
from ..deps import get_weather_service
from ..models.common import AppError

router = APIRouter(tags=["weather"])


@router.get("/circuits")
async def circuits(svc=Depends(get_weather_service)):
    return {"circuits": svc.get_all_circuits()}


@router.get("/current/{circuit:path}")
async def current_weather(circuit: str, svc=Depends(get_weather_service)):
    data = await svc.get_circuit_weather(circuit)
    return data


@router.get("/race-weekend/{circuit:path}")
async def race_weekend_weather(circuit: str, svc=Depends(get_weather_service)):
    return await svc.get_race_weekend_weather(circuit)
