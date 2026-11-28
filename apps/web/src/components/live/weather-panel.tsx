export interface LiveWeather {
  airTempC: number | null;
  trackTempC: number | null;
  rainfall: boolean | null;
}

// The live stream state carries no weather yet (the reducer drops weather events), so the
// page passes null and the panel renders nothing rather than an empty box.
export function WeatherPanel({ weather }: { weather: LiveWeather | null }) {
  if (!weather) return null;
  const temp = (v: number | null) => (v === null ? "—" : `${v.toFixed(1)}°C`);
  return (
    <dl className="grid grid-cols-3 gap-3 text-sm">
      <div>
        <dt className="text-carbon-500">Air</dt>
        <dd className="tabular">{temp(weather.airTempC)}</dd>
      </div>
      <div>
        <dt className="text-carbon-500">Track</dt>
        <dd className="tabular">{temp(weather.trackTempC)}</dd>
      </div>
      <div>
        <dt className="text-carbon-500">Rain</dt>
        <dd>{weather.rainfall === null ? "—" : weather.rainfall ? "Yes" : "No"}</dd>
      </div>
    </dl>
  );
}
