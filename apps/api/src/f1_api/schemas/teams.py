import uuid

from pydantic import BaseModel

from f1_api.schemas.standings import DriverRef


class TeamStandingPoint(BaseModel):
    season: int
    round: int
    position: int
    points: float
    wins: int


class TeamProfile(BaseModel):
    id: uuid.UUID
    ref: str
    name: str
    nationality: str | None
    color: str
    drivers: list[DriverRef]
    standings_history: list[TeamStandingPoint]
