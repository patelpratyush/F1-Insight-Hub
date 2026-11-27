export function SeasonNote({
  shownSeason, requestedSeason, currentYear,
}: { shownSeason: number | null; requestedSeason: number | null; currentYear: number }) {
  if (shownSeason === null || requestedSeason !== null || shownSeason === currentYear) return null;
  return (
    <p className="text-sm text-carbon-500">
      {`Showing ${shownSeason} standings. The ${currentYear} season has no results yet.`}
    </p>
  );
}
