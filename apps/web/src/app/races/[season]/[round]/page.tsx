import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { cache } from "react";
import { Card, Tabs, TabsContent, TabsList, TabsTrigger } from "@f1/ui";
import { SessionList } from "@/components/calendar-grid";
import { RaceResults } from "@/components/race-results";
import { getApi, PUBLIC } from "@/lib/api";

type Params = Promise<{ season: string; round: string }>;

const load = cache(async (season: string, round: string) => {
  if (!/^\d{4}$/.test(season) || !/^\d{1,2}$/.test(round)) notFound();
  const { data, response } = await getApi().GET("/v1/races/{season}/{round}", {
    params: { path: { season: Number(season), round: Number(round) } },
    ...PUBLIC,
  });
  if (response.status === 404 || response.status === 422) notFound();
  if (!data) throw new Error(`race ${season}/${round}: HTTP ${response.status}`);
  return data;
});

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { season, round } = await params;
  const race = await load(season, round);
  return { title: `${race.name} ${race.season}` };
}

export default async function RacePage({ params }: { params: Params }) {
  const { season, round } = await params;
  const race = await load(season, round);
  const tabs = [
    { key: "R", label: "Race" },
    { key: "Q", label: "Qualifying" },
    { key: "SPRINT", label: "Sprint" },
  ].filter((t) => t.key !== "SPRINT" || (race.results.SPRINT ?? []).length > 0);
  const weather = race.weather.at(-1);
  return (
    <section className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-widest text-carbon-500">{race.season} · Round {race.round}</p>
        <h1 className="font-[var(--font-display)] text-4xl font-bold">{race.name}</h1>
        {race.circuit ? <p className="text-carbon-200">{race.circuit.name}, {race.circuit.locality}, {race.circuit.country}</p> : null}
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h2 className="mb-2 text-sm uppercase tracking-widest text-carbon-500">Sessions (your local time)</h2>
          {race.sessions.length > 0 ? <SessionList sessions={race.sessions} /> : <p className="text-carbon-500">No sessions scheduled.</p>}
        </Card>
        <Card>
          <h2 className="mb-2 text-sm uppercase tracking-widest text-carbon-500">Weather</h2>
          {weather ? (
            <dl className="grid grid-cols-2 gap-1 text-sm">
              <dt>Air</dt><dd className="tabular">{weather.air_temp_c ?? "—"} °C</dd>
              <dt>Track</dt><dd className="tabular">{weather.track_temp_c ?? "—"} °C</dd>
              <dt>Rain chance</dt><dd className="tabular">{weather.rain_probability ?? "—"} %</dd>
              <dt>Wind</dt><dd className="tabular">{weather.wind_kph ?? "—"} km/h</dd>
            </dl>
          ) : (
            <p className="text-carbon-500">No weather data.</p>
          )}
        </Card>
      </div>
      <Tabs defaultValue="R">
        <TabsList>
          {tabs.map((t) => <TabsTrigger key={t.key} value={t.key}>{t.label}</TabsTrigger>)}
        </TabsList>
        {tabs.map((t) => (
          <TabsContent key={t.key} value={t.key}>
            <RaceResults rows={race.results[t.key] ?? []} showTime={t.key === "Q"} />
          </TabsContent>
        ))}
      </Tabs>
    </section>
  );
}
