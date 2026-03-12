import asyncio
import logging
import os
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="f1tel_")


def _setup_fastf1(cache_dir: str):
    import fastf1
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)


def _clean(data: Any) -> Any:
    """Remove NaN/inf for JSON serialisation."""
    if isinstance(data, (list, tuple)):
        return [_clean(x) for x in data]
    if isinstance(data, dict):
        return {k: _clean(v) for k, v in data.items()}
    if isinstance(data, float) and (np.isnan(data) or np.isinf(data)):
        return None
    if hasattr(data, "item"):       # numpy scalar
        v = data.item()
        return None if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else v
    return data


class TelemetryService:
    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir
        _setup_fastf1(cache_dir)

    def _load_session(self, year: int, race: str, session_type: str, *,
                      laps: bool = True, telemetry: bool = True, weather: bool = True):
        import fastf1
        ses = fastf1.get_session(year, race, session_type)
        ses.load(laps=laps, telemetry=telemetry, weather=weather, messages=False)
        return ses

    # ── analyze ──────────────────────────────────────────────────

    def _analyze(self, year: int, race: str, session_type: str, driver: str) -> Dict:
        ses = self._load_session(year, race, session_type, weather=False)
        laps = ses.laps.pick_drivers(driver)
        if laps.empty:
            return {"error": f"No laps found for {driver}"}
        fastest = laps.pick_fastest()
        tel = fastest.get_telemetry()
        return _clean({
            "driver": driver,
            "lap_time": str(fastest["LapTime"]),
            "sector_1": str(fastest["Sector1Time"]),
            "sector_2": str(fastest["Sector2Time"]),
            "sector_3": str(fastest["Sector3Time"]),
            "max_speed": float(tel["Speed"].max()),
            "min_speed": float(tel["Speed"].min()),
            "avg_speed": float(tel["Speed"].mean()),
            "full_throttle_pct": float((tel["Throttle"] > 95).mean() * 100),
            "braking_pct": float((tel["Brake"] > 50).mean() * 100),
        })

    async def analyze(self, year: int, race: str, session: str, driver: str) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._analyze, year, race, session, driver)

    # ── speed trace ───────────────────────────────────────────────

    def _speed_trace(self, year: int, race: str, session_type: str, driver: str, lap: Optional[int]) -> Dict:
        ses = self._load_session(year, race, session_type, weather=False)
        laps = ses.laps.pick_drivers(driver)
        if laps.empty:
            return {"error": f"No laps for {driver}"}
        target = laps.iloc[lap - 1] if lap else laps.pick_fastest()
        tel = target.get_telemetry()
        return _clean({
            "driver": driver,
            "lap_time": str(target["LapTime"]),
            "distance": tel["Distance"].tolist(),
            "speed":    tel["Speed"].tolist(),
            "throttle": tel["Throttle"].tolist(),
            "brake":    tel["Brake"].tolist(),
            "gear":     tel["nGear"].tolist(),
            "drs":      tel["DRS"].tolist() if "DRS" in tel.columns else [],
        })

    async def speed_trace(self, year: int, race: str, session: str, driver: str, lap: Optional[int] = None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._speed_trace, year, race, session, driver, lap)

    # ── driver comparison ─────────────────────────────────────────

    def _compare(self, year: int, race: str, session_type: str, d1: str, d2: str) -> Dict:
        ses = self._load_session(year, race, session_type, weather=False)
        results = {}
        for drv in (d1, d2):
            laps = ses.laps.pick_drivers(drv)
            if laps.empty:
                results[drv] = {"error": f"No laps for {drv}"}
                continue
            fastest = laps.pick_fastest()
            tel = fastest.get_telemetry()
            results[drv] = _clean({
                "lap_time": str(fastest["LapTime"]),
                "max_speed": float(tel["Speed"].max()),
                "avg_speed": float(tel["Speed"].mean()),
                "full_throttle_pct": float((tel["Throttle"] > 95).mean() * 100),
            })
        return {"driver1": d1, "driver2": d2, "comparison": results}

    async def driver_comparison(self, year: int, race: str, session: str, d1: str, d2: str) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._compare, year, race, session, d1, d2)

    # ── track map ─────────────────────────────────────────────────

    def _track_map(self, year: int, race: str, session_type: str, driver: str, lap: Optional[int]) -> Dict:
        ses = self._load_session(year, race, session_type, weather=False)
        laps = ses.laps.pick_drivers(driver)
        if laps.empty:
            return {"error": f"No laps for {driver}"}
        target = laps.iloc[lap - 1] if lap else laps.pick_fastest()
        tel = target.get_telemetry().add_distance()
        return _clean({
            "driver": driver,
            "x": tel["X"].tolist(),
            "y": tel["Y"].tolist(),
            "speed": tel["Speed"].tolist(),
            "distance": tel["Distance"].tolist(),
        })

    async def track_map(self, year: int, race: str, session: str, driver: str, lap: Optional[int] = None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._track_map, year, race, session, driver, lap)

    # ── weather context ───────────────────────────────────────────

    def _weather(self, year: int, race: str, session_type: str) -> Dict:
        ses = self._load_session(year, race, session_type, laps=False, telemetry=False)
        w = ses.weather_data
        if w is None or w.empty:
            return {"error": "No weather data available"}
        return _clean({
            "air_temp_mean":   float(w["AirTemp"].mean()),
            "air_temp_min":    float(w["AirTemp"].min()),
            "air_temp_max":    float(w["AirTemp"].max()),
            "track_temp_mean": float(w["TrackTemp"].mean()),
            "humidity_mean":   float(w["Humidity"].mean()),
            "rainfall":        bool(w["Rainfall"].any()),
            "wind_speed_mean": float(w["WindSpeed"].mean()),
            "pressure_mean":   float(w["Pressure"].mean()),
        })

    async def weather_context(self, year: int, race: str, session: str) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._weather, year, race, session)

    # ── available sessions ────────────────────────────────────────

    def _available_sessions(self, year: int) -> List[Dict]:
        import fastf1
        try:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
            sessions = []
            for _, event in schedule.iterrows():
                sessions.append({
                    "round": int(event.get("RoundNumber", 0)),
                    "race_name": str(event.get("EventName", "")),
                    "date": str(event.get("EventDate", ""))[:10],
                    "sessions": ["FP1", "FP2", "FP3", "Q", "R"],
                })
            return sessions
        except Exception as e:
            logger.error(f"Failed to get schedule for {year}: {e}")
            return []

    async def available_sessions(self, year: int) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._available_sessions, year)
