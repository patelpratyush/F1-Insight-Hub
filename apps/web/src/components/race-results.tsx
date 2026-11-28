import Link from "next/link";
import type { ResultRow } from "@f1/contract";
import { DataTable } from "@f1/ui";
import { formatLapTime } from "@/lib/format";

/** Results for one session. `time_ms` is shown as a lap time, so pass `showTime` only for qualifying. */
export function RaceResults({ rows, showTime = false }: { rows: ResultRow[]; showTime?: boolean }) {
  if (rows.length === 0) return <p className="py-4 text-carbon-500">Results not available yet</p>;
  return (
    <DataTable>
      <thead>
        <tr>
          <th scope="col">Pos</th>
          <th scope="col">Driver</th>
          <th scope="col">Team</th>
          <th scope="col">Grid</th>
          <th scope="col">{showTime ? "Time" : "Status"}</th>
          <th scope="col" className="text-right">Pts</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.driver.id} className="border-t border-carbon-800">
            <td className="tabular">{r.position ?? "DNF"}</td>
            <td>
              <Link href={`/drivers/${r.driver.ref}`} className="hover:underline">
                {r.driver.given_name} {r.driver.family_name}
              </Link>
            </td>
            <td>
              <Link href={`/teams/${r.team.ref}`} className="text-carbon-200 hover:underline">{r.team.name}</Link>
            </td>
            <td className="tabular">{r.grid ?? "—"}</td>
            <td className="tabular text-carbon-200">{showTime ? formatLapTime(r.time_ms) : r.status}</td>
            <td className="tabular text-right">{r.points}</td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}
