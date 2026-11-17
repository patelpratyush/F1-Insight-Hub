import type { DriverStanding } from "@f1/contract";
import { TimingTowerRow } from "@f1/ui";

export function StandingsTable({ rows }: { rows: DriverStanding[] }) {
  if (rows.length === 0) return <p className="text-carbon-500">No standings available yet.</p>;
  return (
    <div role="table" aria-label="Driver standings">
      {rows.map((r) => {
        const code = (r.driver.code ?? r.driver.family_name).toUpperCase();
        return (
          <TimingTowerRow
            key={r.driver.id}
            position={r.position}
            code={code}
            name={`${r.driver.given_name} ${r.driver.family_name}`}
            value={String(r.points)}
            delta={`${r.wins}W`}
          />
        );
      })}
    </div>
  );
}
