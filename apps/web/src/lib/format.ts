export function formatLapTime(ms: number | null): string {
  if (ms === null) return "—";
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  const millis = ms % 1000;
  const s = String(seconds).padStart(minutes > 0 ? 2 : 1, "0");
  return `${minutes > 0 ? `${minutes}:` : ""}${s}.${String(millis).padStart(3, "0")}`;
}

/** Gaps arrive as strings from the API ("+1 LAP", "+12.346"); never parse them to numbers. */
export const formatGap = (v: string | null): string => (v === null || v === "" ? "—" : v);

/** The API returns UTC; render in the viewer's (or a given) time zone. */
export function formatLocalDateTime(iso: string, locale?: string, timeZone?: string): string {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
    hourCycle: "h23",
  }).format(new Date(iso));
}
