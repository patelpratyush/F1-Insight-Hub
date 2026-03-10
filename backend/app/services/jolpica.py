"""Async Jolpica-F1 API client. One shared aiohttp session for the app lifetime."""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class JolpicaClient:
    def __init__(self, base_url: str = "https://api.jolpi.ca/ergast/f1"):
        self._base = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def open(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Accept": "application/json"},
        )

    async def close(self):
        if self._session:
            await self._session.close()

    # ── Low-level GET ──────────────────────────────────────────────

    async def _get(self, path: str) -> Optional[Dict]:
        if not self._session:
            return None
        url = f"{self._base}/{path}"
        try:
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
                if resp.status == 429:
                    logger.warning(f"Rate limited on {path}, backing off 5s")
                    await asyncio.sleep(5)
                    return None
                logger.warning(f"Jolpica {path} → HTTP {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Jolpica fetch error [{path}]: {e}")
            return None

    # ── Domain fetch methods ──────────────────────────────────────

    async def get_schedule(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}.json")
        if not data:
            return []
        try:
            races_raw = data["MRData"]["RaceTable"]["Races"]
            return [
                {
                    "round": int(r["round"]),
                    "race_name": r["raceName"],
                    "date": r["date"],
                    "circuit": r["Circuit"]["circuitName"],
                    "location": r["Circuit"]["Location"].get("locality", ""),
                    "country": r["Circuit"]["Location"].get("country", ""),
                }
                for r in races_raw
            ]
        except (KeyError, TypeError) as e:
            logger.error(f"parse schedule {year}: {e}")
            return []

    async def get_drivers(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/drivers.json?limit=30")
        if not data:
            return []
        try:
            return [
                {
                    "id": d.get("driverId", ""),
                    "code": d.get("code", ""),
                    "name": f"{d.get('givenName', '')} {d.get('familyName', '')}".strip(),
                    "number": d.get("permanentNumber", ""),
                    "nationality": d.get("nationality", ""),
                }
                for d in data["MRData"]["DriverTable"]["Drivers"]
            ]
        except (KeyError, TypeError) as e:
            logger.error(f"parse drivers {year}: {e}")
            return []

    async def get_constructors(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/constructors.json")
        if not data:
            return []
        try:
            return [
                {
                    "id": c.get("constructorId", ""),
                    "name": c.get("name", ""),
                    "nationality": c.get("nationality", ""),
                }
                for c in data["MRData"]["ConstructorTable"]["Constructors"]
            ]
        except (KeyError, TypeError) as e:
            logger.error(f"parse constructors {year}: {e}")
            return []

    async def get_driver_standings(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/driverStandings.json")
        if not data:
            return []
        try:
            lists = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not lists:
                return []
            return [
                {
                    "position": int(s["position"]),
                    "driver": s["Driver"].get("code", ""),
                    "name": f"{s['Driver'].get('givenName','')} {s['Driver'].get('familyName','')}".strip(),
                    "team": s["Constructors"][0]["name"] if s.get("Constructors") else "Unknown",
                    "points": float(s["points"]),
                    "wins": int(s["wins"]),
                }
                for s in lists[0]["DriverStandings"]
            ]
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"parse driver standings {year}: {e}")
            return []

    async def get_constructor_standings(self, year: int) -> List[Dict]:
        data = await self._get(f"{year}/constructorStandings.json")
        if not data:
            return []
        try:
            lists = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not lists:
                return []
            return [
                {
                    "position": int(s["position"]),
                    "team_name": s["Constructor"].get("name", ""),
                    "points": float(s["points"]),
                    "wins": int(s["wins"]),
                }
                for s in lists[0]["ConstructorStandings"]
            ]
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"parse constructor standings {year}: {e}")
            return []

    async def get_race_result(self, year: int, round_num: int) -> Optional[Dict]:
        data = await self._get(f"{year}/{round_num}/results.json")
        if not data:
            return None
        try:
            races = data["MRData"]["RaceTable"]["Races"]
            if not races:
                return None
            race = races[0]
            results = []
            for r in race.get("Results", []):
                time_str = (r.get("Time") or {}).get("time", "") if isinstance(r.get("Time"), dict) else ""
                results.append({
                    "position": int(r["position"]),
                    "code": r["Driver"].get("code", ""),
                    "name": f"{r['Driver'].get('givenName','')} {r['Driver'].get('familyName','')}".strip(),
                    "team": r["Constructor"].get("name", ""),
                    "points": float(r.get("points", 0)),
                    "time": time_str,
                    "status": r.get("status", ""),
                    "laps": int(r.get("laps", 0)),
                    "grid": int(r.get("grid", 0)),
                })
            fastest = next(
                ({"driver": r["Driver"].get("code",""), "time": (r["FastestLap"]["Time"]["time"] if r.get("FastestLap") else ""), "lap": r.get("FastestLap", {}).get("lap","")}
                 for r in race.get("Results",[]) if r.get("FastestLap",{}).get("rank") == "1"),
                {}
            )
            return {
                "raceName": race.get("raceName", ""),
                "round": int(race.get("round", round_num)),
                "date": race.get("date", ""),
                "location": race.get("Circuit", {}).get("Location", {}).get("locality", ""),
                "results": results,
                "fastestLap": fastest,
            }
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"parse race result {year}/{round_num}: {e}")
            return None
