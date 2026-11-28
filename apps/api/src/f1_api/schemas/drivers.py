import uuid

from pydantic import BaseModel

from f1_api.schemas.races import ResultRow


class DriverSeason(BaseModel):
    year: int
    team: str
    position: int
    points: float
    wins: int


class TeamStintOut(BaseModel):
    team: str
    season: int
    from_round: int
    to_round: int | None


class DriverProfile(BaseModel):
    id: uuid.UUID
    ref: str
    code: str | None
    given_name: str
    family_name: str
    number: int | None
    nationality: str | None
    seasons: list[DriverSeason]
    recent_results: list[ResultRow]
    team_history: list[TeamStintOut]
