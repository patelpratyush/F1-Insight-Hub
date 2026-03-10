"""
Live weather service for F1 circuits.
Ports live_weather_service.py to fully async aiohttp.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Circuit coordinates — ported from live_weather_service.py
CIRCUITS: Dict[str, Dict] = {
    "Bahrain Grand Prix":        {"lat": 26.0325, "lon": 50.5106, "location": "Sakhir",         "country": "Bahrain"},
    "Saudi Arabian Grand Prix":  {"lat": 21.6322, "lon": 39.1044, "location": "Jeddah",          "country": "Saudi Arabia"},
    "Australian Grand Prix":     {"lat": -37.8497,"lon": 144.968,  "location": "Melbourne",       "country": "Australia"},
    "Japanese Grand Prix":       {"lat": 34.8431, "lon": 136.541,  "location": "Suzuka",          "country": "Japan"},
    "Chinese Grand Prix":        {"lat": 31.3389, "lon": 121.220,  "location": "Shanghai",        "country": "China"},
    "Miami Grand Prix":          {"lat": 25.9581, "lon": -80.2389, "location": "Miami",           "country": "USA"},
    "Emilia Romagna Grand Prix": {"lat": 44.3439, "lon": 11.7167,  "location": "Imola",           "country": "Italy"},
    "Monaco Grand Prix":         {"lat": 43.7347, "lon":  7.4205,  "location": "Monte Carlo",     "country": "Monaco"},
    "Canadian Grand Prix":       {"lat": 45.5048, "lon": -73.5225, "location": "Montreal",        "country": "Canada"},
    "Spanish Grand Prix":        {"lat": 41.5700, "lon":  2.2617,  "location": "Barcelona",       "country": "Spain"},
    "Austrian Grand Prix":       {"lat": 47.2197, "lon": 14.7647,  "location": "Spielberg",       "country": "Austria"},
    "British Grand Prix":        {"lat": 52.0786, "lon": -1.0169,  "location": "Silverstone",     "country": "UK"},
    "Hungarian Grand Prix":      {"lat": 47.5830, "lon": 19.2526,  "location": "Budapest",        "country": "Hungary"},
    "Belgian Grand Prix":        {"lat": 50.4372, "lon":  5.9714,  "location": "Spa",             "country": "Belgium"},
    "Dutch Grand Prix":          {"lat": 52.3881, "lon":  4.5400,  "location": "Zandvoort",       "country": "Netherlands"},
    "Italian Grand Prix":        {"lat": 45.6156, "lon":  9.2811,  "location": "Monza",           "country": "Italy"},
    "Azerbaijan Grand Prix":     {"lat": 40.3725, "lon": 49.8533,  "location": "Baku",            "country": "Azerbaijan"},
    "Singapore Grand Prix":      {"lat":  1.2914, "lon": 103.864,  "location": "Singapore",       "country": "Singapore"},
    "United States Grand Prix":  {"lat": 30.1328, "lon": -97.6411, "location": "Austin",          "country": "USA"},
    "Mexico City Grand Prix":    {"lat": 19.4042, "lon": -99.0907, "location": "Mexico City",     "country": "Mexico"},
    "São Paulo Grand Prix":      {"lat": -23.7036,"lon": -46.6997, "location": "São Paulo",       "country": "Brazil"},
    "Las Vegas Grand Prix":      {"lat": 36.1716, "lon": -115.140, "location": "Las Vegas",       "country": "USA"},
    "Qatar Grand Prix":          {"lat": 25.4900, "lon": 51.4542,  "location": "Lusail",          "country": "Qatar"},
    "Abu Dhabi Grand Prix":      {"lat": 24.4672, "lon": 54.6031,  "location": "Yas Marina",      "country": "UAE"},
}

_weather_cache: Dict[str, Dict] = {}  # {circuit: {data, expires}}
CACHE_SECS = 600


class WeatherService:
    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        self._key = api_key
        self._session = session
        self._base = "https://api.openweathermap.org/data/2.5"

    def _cached(self, circuit: str) -> Optional[Dict]:
        entry = _weather_cache.get(circuit)
        if entry and time.time() < entry["expires"]:
            return entry["data"]
        return None

    def _store(self, circuit: str, data: Dict):
        _weather_cache[circuit] = {"data": data, "expires": time.time() + CACHE_SECS}

    async def _owm_get(self, lat: float, lon: float) -> Optional[Dict]:
        if not self._key or not self._session:
            return None
        url = f"{self._base}/weather"
        params = {"lat": lat, "lon": lon, "appid": self._key, "units": "metric"}
        try:
            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning(f"OWM returned {resp.status}")
                return None
        except Exception as e:
            logger.error(f"OWM error: {e}")
            return None

    async def get_circuit_weather(self, circuit: str) -> Dict:
        cached = self._cached(circuit)
        if cached:
            return cached

        meta = CIRCUITS.get(circuit)
        if not meta:
            return _fallback_weather(circuit)

        raw = await self._owm_get(meta["lat"], meta["lon"])
        if not raw:
            return _fallback_weather(circuit, meta)

        data = _parse_owm(circuit, meta, raw)
        self._store(circuit, data)
        return data

    async def get_race_weekend_weather(self, circuit: str) -> Dict:
        current = await self.get_circuit_weather(circuit)
        return {
            "circuit": circuit,
            "current": current,
            "sessions_forecast": {
                "practice_1": _forecast_shift(current, -2),
                "practice_2": _forecast_shift(current, -1),
                "qualifying": _forecast_shift(current, 0),
                "race":       _forecast_shift(current, 1),
            },
        }

    def get_all_circuits(self) -> List[str]:
        return sorted(CIRCUITS.keys())


def _parse_owm(circuit: str, meta: Dict, raw: Dict) -> Dict:
    main = raw.get("main", {})
    wind = raw.get("wind", {})
    weather_list = raw.get("weather", [{}])
    desc = weather_list[0].get("description", "clear")
    rain_1h = raw.get("rain", {}).get("1h", 0.0)

    condition = "clear"
    if rain_1h > 5:
        condition = "heavy_rain"
    elif rain_1h > 0.5:
        condition = "light_rain"
    elif "cloud" in desc:
        condition = "overcast"

    track_temp = main.get("temp", 25) * 1.4  # rough estimation

    return {
        "circuit": circuit,
        "location": meta["location"],
        "country": meta["country"],
        "temperature_c": main.get("temp"),
        "feels_like_c": main.get("feels_like"),
        "humidity_pct": main.get("humidity"),
        "pressure_hpa": main.get("pressure"),
        "wind_speed_ms": wind.get("speed"),
        "wind_direction_deg": wind.get("deg"),
        "condition": condition,
        "description": desc,
        "precipitation_1h_mm": rain_1h,
        "track_temp_estimate_c": round(track_temp, 1),
        "grip_level": "Excellent" if condition == "clear" else "Good" if condition == "overcast" else "Poor",
    }


def _fallback_weather(circuit: str, meta: Dict = None) -> Dict:
    return {
        "circuit": circuit,
        "location": (meta or {}).get("location", "Unknown"),
        "condition": "unknown",
        "description": "Live weather unavailable — no API key or circuit not found",
        "temperature_c": None,
        "humidity_pct": None,
    }


def _forecast_shift(current: Dict, hour_offset: int) -> Dict:
    """Very simple forecast — shift temp slightly, keep condition."""
    result = dict(current)
    t = current.get("temperature_c")
    if t is not None:
        result["temperature_c"] = round(t + hour_offset * 0.5, 1)
    return result
