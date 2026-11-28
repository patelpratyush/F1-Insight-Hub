import Link from "next/link";
import type { RaceSummary } from "@f1/contract";
import { Card } from "@f1/ui";
import { LocalTime } from "./local-time";

const month = new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric", timeZone: "UTC" });

export function SessionList({ sessions }: { sessions: RaceSummary["sessions"] }) {
  return (
    <ul className="space-y-1 text-sm">
      {sessions.map((s) => (
        <li key={s.type} className="flex justify-between gap-3">
          <span className="font-bold">{s.type}</span>
          <span className={s.status === "cancelled" ? "text-carbon-500 line-through" : "text-carbon-200"}>
            <LocalTime iso={s.starts_at} />
          </span>
          {s.status === "cancelled" || s.status === "live" ? <span className="uppercase text-brand">{s.status}</span> : null}
        </li>
      ))}
    </ul>
  );
}

export function CalendarGrid({ races }: { races: RaceSummary[] }) {
  if (races.length === 0) return <p className="text-carbon-500">No races scheduled yet.</p>;
  const groups = new Map<string, RaceSummary[]>();
  for (const r of races) {
    const key = month.format(new Date(`${r.race_date}T00:00:00Z`));
    groups.set(key, [...(groups.get(key) ?? []), r]);
  }
  return (
    <div className="space-y-8">
      {[...groups].map(([label, rs]) => (
        <section key={label} className="space-y-3">
          <h2 className="text-sm uppercase tracking-widest text-carbon-500">{label}</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {rs.map((r) => (
              <Card key={r.round} className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-xs text-carbon-500">Round {r.round}</p>
                    <h3 className="font-[var(--font-display)] text-xl font-bold">
                      <Link href={`/races/${r.season}/${r.round}`} className="hover:underline">{r.name}</Link>
                    </h3>
                    {r.circuit ? <p className="text-sm text-carbon-200">{r.circuit.locality}, {r.circuit.country}</p> : null}
                  </div>
                  {r.sessions.some((s) => s.type === "SPRINT") ? (
                    <span className="rounded bg-team px-2 py-0.5 text-xs font-bold uppercase">Sprint</span>
                  ) : null}
                </div>
                <SessionList sessions={r.sessions} />
              </Card>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
