import type { Metadata } from "next";
import { CalendarGrid } from "@/components/calendar-grid";
import { getApi, PUBLIC } from "@/lib/api";

export const metadata: Metadata = { title: "Calendar" };

export default async function CalendarPage({ searchParams }: { searchParams: Promise<{ season?: string }> }) {
  const { season } = await searchParams;
  const query = season && /^\d{4}$/.test(season) ? { season: Number(season) } : {};
  const { data } = await getApi().GET("/v1/calendar", { params: { query }, ...PUBLIC });
  const races = data ?? [];
  return (
    <section className="space-y-6">
      <h1 className="font-[var(--font-display)] text-4xl font-bold">
        {races[0] ? `${races[0].season} Calendar` : "Calendar"}
      </h1>
      <p className="text-sm text-carbon-500">Session times are shown in your local time.</p>
      <CalendarGrid races={races} />
    </section>
  );
}
