export function getCurrentSeasonYear(referenceDate = new Date()): number {
  return referenceDate.getFullYear();
}

/**
 * True when raceDate (the Sunday race date) falls within a typical race
 * weekend window: from the Friday before through the Sunday itself.
 * Used to switch dashboard queries to faster polling -- this is honest
 * "fast refresh", not true live timing (the underlying data source isn't
 * push/real-time).
 */
export function isRaceWeekend(
  raceDate?: string | null,
  referenceDate = new Date(),
): boolean {
  if (!raceDate) return false;
  const race = new Date(`${raceDate}T00:00:00Z`);
  if (Number.isNaN(race.getTime())) return false;

  const msPerDay = 24 * 60 * 60 * 1000;
  const diffDays = (race.getTime() - referenceDate.getTime()) / msPerDay;
  // Race is Sunday; weekend window opens the Friday before (2 days prior)
  // and closes at the end of race day.
  return diffDays <= 2 && diffDays >= -1;
}

export function getRaceDisplayName(raceName?: string | null): string {
  if (!raceName) return "TBD";
  return raceName.replace(/\s+Grand Prix$/, "").trim() || raceName;
}

export function formatRaceDate(
  dateValue?: string | null,
  locale = "en-US",
): string {
  if (!dateValue) return "N/A";

  const parsedDate = /^\d{4}-\d{2}-\d{2}$/.test(dateValue)
    ? new Date(`${dateValue}T12:00:00Z`)
    : new Date(dateValue);
  if (Number.isNaN(parsedDate.getTime())) return "N/A";

  return parsedDate.toLocaleDateString(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface DefaultCircuitOptions {
  nextRaceName?: string | null;
  dashboardUpcomingRaceName?: string | null;
  availableCircuits?: string[];
}

export function getDefaultCircuitName({
  nextRaceName,
  dashboardUpcomingRaceName,
  availableCircuits = [],
}: DefaultCircuitOptions): string {
  return (
    nextRaceName ||
    dashboardUpcomingRaceName ||
    availableCircuits.find(Boolean) ||
    ""
  );
}

export function getSeasonDataStatus(
  requestedYear: number,
  resolvedDataYear?: number | null,
) {
  const dataYear = resolvedDataYear ?? requestedYear;

  return {
    requestedYear,
    dataYear,
    hasHistoricalFallback: dataYear !== requestedYear,
  };
}

export function getNextSelectedDrivers(
  currentSelected: string[],
  availableDriverCodes: string[],
  maxSelected = 6,
): string[] {
  if (!availableDriverCodes.length) return currentSelected;

  const validSelections = currentSelected.filter((code) =>
    availableDriverCodes.includes(code),
  );
  const nextSelected =
    validSelections.length > 0
      ? validSelections
      : availableDriverCodes.slice(0, maxSelected);

  if (
    nextSelected.length === currentSelected.length &&
    nextSelected.every((code, index) => code === currentSelected[index])
  ) {
    return currentSelected;
  }

  return nextSelected;
}
