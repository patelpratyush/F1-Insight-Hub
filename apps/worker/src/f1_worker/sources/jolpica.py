import asyncio
from dataclasses import dataclass
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
