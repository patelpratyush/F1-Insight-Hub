import uuid
from datetime import datetime

from f1_db.models import Driver, Team
from pydantic import BaseModel


class DriverRef(BaseModel):
    id: uuid.UUID
    ref: str
    code: str | None
    given_name: str
    family_name: str
    number: int | None

    @classmethod
    def of(cls, d: Driver) -> "DriverRef":
        return cls(
            id=d.id,
            ref=d.ref,
            code=d.code,
            given_name=d.given_name,
            family_name=d.family_name,
            number=d.number,
        )


class TeamRef(BaseModel):
    id: uuid.UUID
    ref: str
    name: str

    @classmethod
    def of(cls, t: Team) -> "TeamRef":
        return cls(id=t.id, ref=t.ref, name=t.name)


class DriverStandingOut(BaseModel):
    position: int
    points: float
    wins: int
    driver: DriverRef
    team: TeamRef
    season: int
    round: int
    updated_at: datetime


class ConstructorStandingOut(BaseModel):
    position: int
    points: float
    wins: int
    team: TeamRef
    season: int
    round: int
    updated_at: datetime
