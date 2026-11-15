export function FreshnessLabel({ lastSuccessAt, now = new Date() }: { lastSuccessAt: string | null; now?: Date }) {
  if (!lastSuccessAt) return <span className="text-carbon-500">No data yet</span>;
  const minutes = Math.max(0, Math.round((now.getTime() - new Date(lastSuccessAt).getTime()) / 60000));
  if (minutes > 120) return <span className="text-timing-yellow">Data may be stale</span>;
  const text = minutes < 1 ? "Updated just now" : `Updated ${minutes} min ago`;
  return <span className="text-carbon-500">{text}</span>;
}
