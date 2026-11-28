import Link from "next/link";
import { Button } from "@f1/ui";
import { NextRaceCard } from "@/components/next-race-card";
import { pickNextRace } from "@/lib/next-race";
import { getApi, PUBLIC } from "@/lib/api";

export default async function Home() {
  // Prerendered at build time, when the API may be unreachable: render the empty state then.
  const { data } = await getApi()
    .GET("/v1/calendar", { params: { query: {} }, ...PUBLIC })
    .catch(() => ({ data: undefined }));
  const now = new Date();
  return (
    <section className="space-y-6 py-8">
      <h1 className="font-[var(--font-display)] text-5xl font-extrabold tracking-wide">F1 INSIGHT HUB</h1>
      <NextRaceCard race={pickNextRace(data ?? [], now)} now={now} />
      <div className="flex gap-3">
        <Button asChild><Link href="/calendar">Full calendar</Link></Button>
        <Button asChild><Link href="/standings" prefetch={false}>View standings</Link></Button>
      </div>
    </section>
  );
}
