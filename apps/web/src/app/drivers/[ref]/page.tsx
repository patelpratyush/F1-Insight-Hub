import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { cache } from "react";
import { Card, DataTable } from "@f1/ui";
import { DriverHeader } from "@/components/driver-header";
import { TeamTheme } from "@/components/team-theme";
import { getApi, PUBLIC } from "@/lib/api";

type Params = Promise<{ ref: string }>;

const load = cache(async (ref: string) => {
  const { data, response } = await getApi().GET("/v1/drivers/{ref}", { params: { path: { ref } }, ...PUBLIC });
  if (response.status === 404) notFound();
  if (!data) throw new Error(`driver ${ref}: HTTP ${response.status}`);
  return data;
});

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const d = await load((await params).ref);
  return { title: `${d.given_name} ${d.family_name}` };
}

export default async function DriverPage({ params }: { params: Params }) {
  const driver = await load((await params).ref);
  // The profile has no colour of its own: theme by the team of the latest race.
  const team = driver.recent_results[0]?.team ?? null;
  const color = team
    ? (await getApi().GET("/v1/teams/{ref}", { params: { path: { ref: team.ref } }, ...PUBLIC })).data?.color
    : undefined;
  const body = (
    <section className="space-y-6">
      <DriverHeader driver={driver} team={team} />
      <Card>
        <h2 className="mb-2 text-sm uppercase tracking-widest text-carbon-500">Recent races</h2>
        {driver.recent_results.length > 0 ? (
          <ol className="flex flex-wrap gap-2">
            {driver.recent_results.map((r, i) => (
              <li key={i} title={r.status} className="tabular rounded bg-carbon-800 px-2 py-1 text-sm">
                {r.position !== null ? `P${r.position}` : "DNF"}
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-carbon-500">No results yet.</p>
        )}
      </Card>
      <Card>
        <h2 className="mb-2 text-sm uppercase tracking-widest text-carbon-500">Seasons</h2>
        {driver.seasons.length > 0 ? (
          <DataTable>
            <thead>
              <tr><th scope="col">Year</th><th scope="col">Team</th><th scope="col">Pos</th><th scope="col">Wins</th><th scope="col" className="text-right">Pts</th></tr>
            </thead>
            <tbody>
              {driver.seasons.map((s) => (
                <tr key={s.year} className="border-t border-carbon-800">
                  <td className="tabular">{s.year}</td><td>{s.team}</td><td className="tabular">{s.position}</td>
                  <td className="tabular">{s.wins}</td><td className="tabular text-right">{s.points}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : (
          <p className="text-carbon-500">No standings yet.</p>
        )}
      </Card>
      {driver.team_history.length > 0 ? (
        <Card>
          <h2 className="mb-2 text-sm uppercase tracking-widest text-carbon-500">Teams</h2>
          <ul className="space-y-1 text-sm">
            {driver.team_history.map((t) => (
              <li key={`${t.season}-${t.from_round}`}>
                {t.season} · {t.team} · rounds {t.from_round}–{t.to_round ?? "now"}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </section>
  );
  return color ? <TeamTheme color={color}>{body}</TeamTheme> : body;
}
