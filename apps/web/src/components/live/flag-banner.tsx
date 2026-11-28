const styles: Record<string, string> = {
  YELLOW: "bg-timing-yellow text-carbon-950",
  "DOUBLE YELLOW": "bg-timing-yellow text-carbon-950",
  RED: "bg-brand text-carbon-50",
  CHEQUERED: "bg-carbon-50 text-carbon-950",
};

/** Track-wide race control flag; nothing is shown under green/clear. */
export function FlagBanner({ flag }: { flag: string }) {
  const style = styles[flag];
  if (!style) return null;
  return (
    <div role="status" className={`rounded px-4 py-2 font-[var(--font-display)] text-lg font-bold uppercase ${style}`}>
      {flag} flag
    </div>
  );
}
