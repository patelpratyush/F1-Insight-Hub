import Link from "next/link";
import { Button } from "@f1/ui";

export default function Home() {
  return (
    <section className="space-y-6 py-16">
      <h1 className="font-[var(--font-display)] text-6xl font-extrabold tracking-wide">F1 INSIGHT HUB</h1>
      <p className="text-carbon-200">Standings, telemetry, predictions, and fantasy. Rebuilt from zero.</p>
      <Button asChild><Link href="/standings">View standings</Link></Button>
    </section>
  );
}
