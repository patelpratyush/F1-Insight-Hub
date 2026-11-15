import uuid
from datetime import datetime

from pydantic import BaseModel


class DriverRef(BaseModel):
    id: uuid.UUID
    code: str | None
    given_name: str
    family_name: str
    number: int | None


class TeamRef(BaseModel):
    id: uuid.UUID
    name: str


class DriverStandingOut(BaseModel):
    position: int
    points: float
    wins: int
    driver: DriverRef
    team: TeamRef
    season: int
    round: int
    updated_at: datetime
