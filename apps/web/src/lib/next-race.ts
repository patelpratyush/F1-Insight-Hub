import type { RaceSummary } from "@f1/contract";

type Session = RaceSummary["sessions"][number];

export const isAhead = (s: Session, now: Date) => s.status !== "cancelled" && new Date(s.starts_at) > now;

/** First race with a live or upcoming session, else the season's last race. */
export function pickNextRace(races: RaceSummary[], now: Date): RaceSummary | null {
  return races.find((r) => r.sessions.some((s) => s.status === "live" || isAhead(s, now))) ?? races.at(-1) ?? null;
}
