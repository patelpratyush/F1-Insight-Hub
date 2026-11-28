import Link from "next/link";
import type { DriverProfile, ResultRow } from "@f1/contract";

export function DriverHeader({ driver, team }: { driver: DriverProfile; team: ResultRow["team"] | null }) {
  return (
    <header data-testid="driver-header" className="flex items-end gap-4 border-l-4 border-team pl-4">
      {driver.number !== null ? (
        <span className="tabular text-6xl font-bold text-team">{driver.number}</span>
      ) : null}
      <div>
        <p className="text-xs uppercase tracking-widest text-carbon-500">
          {[driver.code, driver.nationality].filter(Boolean).join(" · ")}
        </p>
        <h1 className="font-[var(--font-display)] text-4xl font-bold">
          {driver.given_name} {driver.family_name}
        </h1>
        {team ? <Link href={`/teams/${team.ref}`} className="text-carbon-200 hover:underline">{team.name}</Link> : null}
      </div>
    </header>
  );
}
