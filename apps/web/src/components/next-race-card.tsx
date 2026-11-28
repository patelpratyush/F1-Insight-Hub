"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { RaceSummary } from "@f1/contract";
import { Card } from "@f1/ui";
import { isAhead as ahead } from "@/lib/next-race";
import { LocalTime } from "./local-time";

function countdown(ms: number): string {
  const s = Math.floor(ms / 1000);
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${s % 60}s`;
}

export function NextRaceCard({ race, now: initialNow }: { race: RaceSummary | null; now: Date }) {
  const [now, setNow] = useState(initialNow);
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  if (!race) return <Card><p className="text-carbon-500">No races scheduled yet.</p></Card>;
  const live = race.sessions.find((s) => s.status === "live");
  const next = race.sessions
    .filter((s) => ahead(s, now))
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at))[0];
  return (
    <Card className="space-y-2 border-l-4 border-l-team">
      <p className="text-xs uppercase tracking-widest text-carbon-500">
        {live || next ? `Round ${race.round}` : "Season complete"}
      </p>
      <h2 className="font-[var(--font-display)] text-3xl font-bold">
        <Link href={`/races/${race.season}/${race.round}`} className="hover:underline">{race.name}</Link>
      </h2>
      {race.circuit ? <p className="text-carbon-200">{race.circuit.name}, {race.circuit.country}</p> : null}
      {live ? (
        <p className="font-bold text-brand">Live now</p>
      ) : next ? (
        <p className="tabular">
          {next.type} · <LocalTime iso={next.starts_at} /> · Starts in {countdown(new Date(next.starts_at).getTime() - now.getTime())}
        </p>
      ) : (
        <p className="text-carbon-200">Last race {race.race_date}</p>
      )}
    </Card>
  );
}
