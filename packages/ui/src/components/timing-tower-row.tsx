import { cn } from "../lib/cn";

export interface TimingTowerRowProps {
  position: number;
  code: string;
  name: string;
  value: string;
  delta?: string;
  teamColor?: string;
  sector?: "purple" | "green" | "yellow" | "none";
}

const sectorClass = {
  purple: "bg-timing-purple",
  green: "bg-timing-green",
  yellow: "bg-timing-yellow",
  none: "bg-carbon-700",
} as const;

export function TimingTowerRow({
  position, code, name, value, delta, teamColor, sector = "none",
}: TimingTowerRowProps) {
  return (
    <div
      role="row"
      aria-label={`${position} ${code} ${name} ${value}`}
      className="grid grid-cols-[2.5rem_4px_1fr_auto_auto] items-center gap-3 border-b border-carbon-800 px-3 py-2 transition-transform duration-200 ease-[var(--ease-spring)]"
    >
      <span className="tabular text-right text-carbon-200">{position}</span>
      <span aria-hidden className="h-6 w-1 rounded" style={{ background: teamColor ?? "var(--team)" }} />
      <span className="flex items-baseline gap-2">
        <span className="font-[var(--font-display)] text-xl font-bold tracking-wide">{code}</span>
        <span className="text-sm text-carbon-200">{name}</span>
      </span>
      <span className="tabular">{value}</span>
      {delta ? <span className="tabular text-xs text-carbon-500">{delta}</span> : <span />}
      <span data-testid="sector-bar" aria-hidden className={cn("col-span-5 h-0.5 rounded", sectorClass[sector])} />
    </div>
  );
}
