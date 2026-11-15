import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { FreshnessLabel } from "@/components/freshness-label";
import { StandingsTable } from "@/components/standings-table";
import { auth } from "@/lib/auth";
import { getApi } from "@/lib/api";

export default async function StandingsPage() {
  const h = await headers();
  const session = await auth.api.getSession({ headers: h });
  if (!session) redirect("/sign-in?next=/standings");
  const { token } = await auth.api.getToken({ headers: h });
  const api = getApi(token);
  const [standings, fresh] = await Promise.all([
    api.GET("/v1/standings/drivers", {}),
    api.GET("/v1/meta/freshness", {}),
  ]);
  const last = fresh.data?.find((f) => f.job === "standings")?.last_success_at ?? null;
  return (
    <section className="space-y-4">
      <header className="flex items-end justify-between">
        <h1 className="font-[var(--font-display)] text-4xl font-bold">Driver Standings</h1>
        <FreshnessLabel lastSuccessAt={last} />
      </header>
      <StandingsTable rows={standings.data ?? []} />
    </section>
  );
}
