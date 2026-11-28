from datetime import date, datetime

from pydantic import BaseModel


class CircuitOut(BaseModel):
    ref: str
    name: str
    locality: str
    country: str
    lat: float
    lon: float


class SessionOut(BaseModel):
    type: str
    starts_at: datetime  # UTC; the web app renders it in the viewer's timezone
    status: str
    openf1_session_key: int | None = None  # set once matched; web links /live/{key}


class RaceSummary(BaseModel):
    season: int
    round: int
    name: str
    circuit: CircuitOut | None
    race_date: date
    sessions: list[SessionOut]
