import { cn } from "../lib/cn";

type Sector = "purple" | "green" | "yellow" | "none";

export interface TimingTowerRowProps {
  position: number | null;
  code: string;
  name: string;
  value: string;
  delta?: string;
  teamColor?: string;
  sector?: Sector;
  /** Live timing: one bar per sector, replacing the single `sector` bar. */
  sectors?: readonly [Sector, Sector, Sector];
  chip?: "PIT" | "OUT";
  /** Tyre compound, e.g. "SOFT"; shown as a coloured dot. */
  compound?: string | null;
}

const compoundClass: Record<string, string> = {
  SOFT: "bg-brand",
  MEDIUM: "bg-timing-yellow",
  HARD: "bg-carbon-50",
  INTERMEDIATE: "bg-timing-green",
  WET: "bg-sky-500",
};

const sectorClass = {
  purple: "bg-timing-purple",
  green: "bg-timing-green",
  yellow: "bg-timing-yellow",
  none: "bg-carbon-700",
} as const;

export function TimingTowerRow({
  position, code, name, value, delta, teamColor, sector = "none", sectors, chip, compound,
}: TimingTowerRowProps) {
  const pos = position ?? "—";
  return (
    <div
      role="row"
      aria-label={`${pos} ${code} ${name} ${value}`}
      className="grid grid-cols-[2.5rem_4px_1fr_auto_auto] items-center gap-3 border-b border-carbon-800 px-3 py-2 transition-transform duration-200 ease-[var(--ease-spring)]"
    >
      <span className="tabular text-right text-carbon-200">{pos}</span>
      <span aria-hidden className="h-6 w-1 rounded" style={{ background: teamColor ?? "var(--team)" }} />
      <span className="flex items-baseline gap-2">
        <span className="font-[var(--font-display)] text-xl font-bold tracking-wide">{code}</span>
        <span className="text-sm text-carbon-200">{name}</span>
        {compound ? (
          <span
            title={compound}
            aria-label={`${compound} tyre`}
            className={cn("inline-block h-2.5 w-2.5 self-center rounded-full", compoundClass[compound] ?? "bg-carbon-500")}
          />
        ) : null}
        {chip ? (
          <span className={cn("rounded px-1.5 text-xs font-bold", chip === "OUT" ? "bg-carbon-700 text-carbon-200" : "bg-timing-yellow text-carbon-950")}>
            {chip}
          </span>
        ) : null}
      </span>
      <span className="tabular">{value}</span>
      {delta ? <span className="tabular text-xs text-carbon-500">{delta}</span> : <span />}
      {sectors ? (
        <span aria-hidden className="col-span-5 grid grid-cols-3 gap-1">
          {sectors.map((s, i) => (
            <span key={i} data-testid="sector-bar" className={cn("h-0.5 rounded", sectorClass[s])} />
          ))}
        </span>
      ) : (
        <span data-testid="sector-bar" aria-hidden className={cn("col-span-5 h-0.5 rounded", sectorClass[sector])} />
      )}
    </div>
  );
}
