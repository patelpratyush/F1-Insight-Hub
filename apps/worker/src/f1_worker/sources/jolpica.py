import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import httpx

from f1_worker.resilience import CircuitBreaker


@dataclass(frozen=True)
class ParsedStanding:
    round: int
    position: int
    points: Decimal
    wins: int
    driver_ref: str
    driver_code: str | None
    given_name: str
    family_name: str
    number: int | None
    driver_nationality: str | None
    team_ref: str
    team_name: str
    team_nationality: str | None


SESSION_KEYS = {
    "FirstPractice": "FP1",
    "SecondPractice": "FP2",
    "ThirdPractice": "FP3",
    "SprintQualifying": "SQ",
    "SprintShootout": "SQ",
    "Sprint": "SPRINT",
    "Qualifying": "Q",
}


@dataclass(frozen=True)
class ParsedRace:
    round: int
    name: str
    circuit_ref: str
    circuit_name: str
    locality: str
    country: str
    lat: float
    lon: float
    race_date: date
    sessions: dict[str, datetime]


@dataclass(frozen=True)
class ParsedResult:
    session_type: str  # R | Q | SPRINT
    driver_ref: str
    driver_code: str | None
    given_name: str
    family_name: str
    number: int | None
    driver_nationality: str | None
    team_ref: str
    team_name: str
    team_nationality: str | None
    position: int | None  # None when not classified (positionText R, D, W, ...)
    grid: int | None
    status: str
    points: Decimal
    time_ms: int | None


@dataclass(frozen=True)
class ParsedConstructorStanding:
    round: int
    position: int
    points: Decimal
    wins: int
    team_ref: str
    team_name: str
    team_nationality: str | None


def _result(session_type: str, item: dict[str, Any]) -> ParsedResult:
    d, c = item["Driver"], item["Constructor"]
    number = d.get("permanentNumber")
    grid = item.get("grid")
    millis = (item.get("Time") or {}).get("millis")
    return ParsedResult(
        session_type=session_type,
        driver_ref=d["driverId"],
        driver_code=d.get("code"),
        given_name=d["givenName"],
        family_name=d["familyName"],
        number=int(number) if number else None,
        driver_nationality=d.get("nationality"),
        team_ref=c["constructorId"],
        team_name=c["name"],
        team_nationality=c.get("nationality"),
        position=int(item["position"]) if str(item.get("positionText", "")).isdigit() else None,
        grid=int(grid) if grid not in (None, "") else None,
        status=item.get("status", "Finished"),
        points=Decimal(item.get("points", "0")),
        time_ms=int(millis) if millis else None,
    )


def _dt(block: dict[str, str]) -> datetime:
    time = block.get("time", "00:00:00Z").replace("Z", "+00:00")
    return datetime.fromisoformat(f"{block['date']}T{time}").astimezone(UTC)


class JolpicaClient:
    def __init__(
        self,
        base_url: str = "https://api.jolpi.ca/ergast/f1",
        client: httpx.AsyncClient | None = None,
        breaker: CircuitBreaker | None = None,
        retry_wait: float = 0.5,
        attempts: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        self.breaker = breaker or CircuitBreaker(failure_threshold=5, reset_seconds=60)
        self.retry_wait = retry_wait
        self.attempts = attempts

    async def _get_json(self, path: str) -> dict[str, Any]:
        async def attempt() -> dict[str, Any]:
            last: httpx.Response | None = None
            for n in range(self.attempts):
                resp = await self.client.get(f"{self.base_url}{path}")
                if resp.status_code not in (429, 500, 502, 503, 504):
                    resp.raise_for_status()
                    data: dict[str, Any] = resp.json()
                    return data
                last = resp
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else self.retry_wait * (2**n)
                if self.retry_wait == 0:
                    wait = 0
                if n < self.attempts - 1:
                    await asyncio.sleep(wait)
            assert last is not None
            last.raise_for_status()
            raise AssertionError("unreachable")

        return await self.breaker.call(attempt)

    async def driver_standings(self, year: int) -> list[ParsedStanding]:
        data = await self._get_json(f"/{year}/driverStandings.json")
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not lists:
            return []
        block = lists[0]
        rnd = int(block["round"])
        out: list[ParsedStanding] = []
        for item in block["DriverStandings"]:
            d, c = item["Driver"], item["Constructors"][0]
            number = d.get("permanentNumber")
            out.append(
                ParsedStanding(
                    round=rnd,
                    position=int(item["position"]),
                    points=Decimal(item["points"]),
                    wins=int(item["wins"]),
                    driver_ref=d["driverId"],
                    driver_code=d.get("code"),
                    given_name=d["givenName"],
                    family_name=d["familyName"],
                    number=int(number) if number else None,
                    driver_nationality=d.get("nationality"),
                    team_ref=c["constructorId"],
                    team_name=c["name"],
                    team_nationality=c.get("nationality"),
                )
            )
        return out

    async def calendar(self, year: int) -> list[ParsedRace]:
        data = await self._get_json(f"/{year}.json")
        out: list[ParsedRace] = []
        for r in data["MRData"]["RaceTable"]["Races"]:
            circuit, loc = r["Circuit"], r["Circuit"]["Location"]
            sessions = {key: _dt(r[name]) for name, key in SESSION_KEYS.items() if name in r}
            sessions["R"] = _dt({"date": r["date"], "time": r.get("time", "00:00:00Z")})
            out.append(
                ParsedRace(
                    round=int(r["round"]),
                    name=r["raceName"],
                    circuit_ref=circuit["circuitId"],
                    circuit_name=circuit["circuitName"],
                    locality=loc["locality"],
                    country=loc["country"],
                    lat=float(loc["lat"]),
                    lon=float(loc["long"]),
                    race_date=date.fromisoformat(r["date"]),
                    sessions=sessions,
                )
            )
        return out

    async def _session_results(
        self, year: int, rnd: int, path: str, key: str, session_type: str
    ) -> list[ParsedResult]:
        data = await self._get_json(f"/{year}/{rnd}/{path}.json")
        races = data["MRData"]["RaceTable"]["Races"]
        if not races:
            return []
        return [_result(session_type, item) for item in races[0].get(key, [])]

    async def results(self, year: int, rnd: int) -> list[ParsedResult]:
        return await self._session_results(year, rnd, "results", "Results", "R")

    async def qualifying(self, year: int, rnd: int) -> list[ParsedResult]:
        return await self._session_results(year, rnd, "qualifying", "QualifyingResults", "Q")

    async def sprint(self, year: int, rnd: int) -> list[ParsedResult]:
        return await self._session_results(year, rnd, "sprint", "SprintResults", "SPRINT")

    async def constructor_standings(self, year: int) -> list[ParsedConstructorStanding]:
        data = await self._get_json(f"/{year}/constructorStandings.json")
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not lists:
            return []
        block = lists[0]
        rnd = int(block["round"])
        return [
            ParsedConstructorStanding(
                round=rnd,
                position=int(item["position"]),
                points=Decimal(item["points"]),
                wins=int(item["wins"]),
                team_ref=item["Constructor"]["constructorId"],
                team_name=item["Constructor"]["name"],
                team_nationality=item["Constructor"].get("nationality"),
            )
            for item in block["ConstructorStandings"]
        ]
