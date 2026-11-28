import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";
import { Card, DataTable } from "@f1/ui";
import { TeamTheme } from "@/components/team-theme";
import { getApi, PUBLIC } from "@/lib/api";

type Params = Promise<{ ref: string }>;

const load = cache(async (ref: string) => {
  const { data, response } = await getApi().GET("/v1/teams/{ref}", { params: { path: { ref } }, ...PUBLIC });
  if (response.status === 404) notFound();
  if (!data) throw new Error(`team ${ref}: HTTP ${response.status}`);
  return data;
});

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  return { title: (await load((await params).ref)).name };
}

export default async function TeamPage({ params }: { params: Params }) {
  const team = await load((await params).ref);
  return (
    <TeamTheme color={team.color}>
      <section className="space-y-6">
        <header data-testid="team-header" className="border-l-4 border-team pl-4">
          <p className="text-xs uppercase tracking-widest text-carbon-500">{team.nationality ?? "Team"}</p>
          <h1 className="font-[var(--font-display)] text-4xl font-bold">{team.name}</h1>
        </header>
        <Card>
          <h2 className="mb-2 text-sm uppercase tracking-widest text-carbon-500">Drivers</h2>
          {team.drivers.length > 0 ? (
            <ul className="space-y-1">
              {team.drivers.map((d) => (
                <li key={d.id}>
                  <Link href={`/drivers/${d.ref}`} className="hover:underline">{d.given_name} {d.family_name}</Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-carbon-500">No drivers yet.</p>
          )}
        </Card>
        <Card>
          <h2 className="mb-2 text-sm uppercase tracking-widest text-carbon-500">Constructor standings</h2>
          {team.standings_history.length > 0 ? (
            <DataTable>
              <thead>
                <tr><th scope="col">Year</th><th scope="col">Pos</th><th scope="col">Wins</th><th scope="col" className="text-right">Pts</th></tr>
              </thead>
              <tbody>
                {team.standings_history.map((s) => (
                  <tr key={s.season} className="border-t border-carbon-800">
                    <td className="tabular">{s.season}</td><td className="tabular">{s.position}</td>
                    <td className="tabular">{s.wins}</td><td className="tabular text-right">{s.points}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          ) : (
            <p className="text-carbon-500">No standings yet.</p>
          )}
        </Card>
      </section>
    </TeamTheme>
  );
}
