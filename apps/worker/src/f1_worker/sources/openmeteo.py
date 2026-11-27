from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import httpx

from f1_worker.resilience import CircuitBreaker


@dataclass(frozen=True)
class WeatherPoint:
    observed_at: datetime
    air_temp_c: float | None
    humidity: float | None
    wind_kph: float | None
    rain_probability: float | None


def _f(v: Any) -> float | None:
    return None if v is None else float(v)


HOURLY = (
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "precipitation_probability",
)


class OpenMeteoClient:
    URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(timeout=10.0)
        self.breaker = CircuitBreaker(failure_threshold=5, reset_seconds=60)

    async def forecast(self, lat: float, lon: float, start: date, end: date) -> list[WeatherPoint]:
        params: dict[str, str | float] = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "UTC",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": ",".join(HOURLY),
        }

        async def go() -> dict[str, Any]:
            resp = await self.client.get(self.URL, params=params)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data

        h = (await self.breaker.call(go))["hourly"]
        return [
            WeatherPoint(
                observed_at=datetime.fromisoformat(t).replace(tzinfo=UTC),
                air_temp_c=_f(h["temperature_2m"][i]),
                humidity=_f(h["relative_humidity_2m"][i]),
                wind_kph=_f(h["wind_speed_10m"][i]),
                rain_probability=_f(h["precipitation_probability"][i]),
            )
            for i, t in enumerate(h["time"])
        ]
