import {
  formatRaceDate,
  getCurrentSeasonYear,
  getDefaultCircuitName,
  getNextSelectedDrivers,
  getRaceDisplayName,
  getSeasonDataStatus,
} from "@/lib/season";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("season helpers", () => {
  it("uses the reference date to resolve the current season year", () => {
    expect(getCurrentSeasonYear(new Date("2026-03-05T12:00:00Z"))).toBe(2026);
  });

  it("formats race names for compact dashboard display", () => {
    expect(getRaceDisplayName("Australian Grand Prix")).toBe("Australian");
    expect(getRaceDisplayName("Sprint Shootout")).toBe("Sprint Shootout");
  });

  it("formats ISO race dates for display", () => {
    expect(formatRaceDate("2026-03-15")).toBe("Mar 15, 2026");
    expect(formatRaceDate("")).toBe("N/A");
  });

  it("prefers the next race when selecting the live circuit context", () => {
    expect(
      getDefaultCircuitName({
        nextRaceName: "Australian Grand Prix",
        dashboardUpcomingRaceName: "Chinese Grand Prix",
        availableCircuits: ["Monaco Grand Prix"],
      }),
    ).toBe("Australian Grand Prix");
  });

  it("falls back through upcoming race and available circuits", () => {
    expect(
      getDefaultCircuitName({
        nextRaceName: "",
        dashboardUpcomingRaceName: "Chinese Grand Prix",
        availableCircuits: ["Monaco Grand Prix"],
      }),
    ).toBe("Chinese Grand Prix");

    expect(
      getDefaultCircuitName({
        nextRaceName: "",
        dashboardUpcomingRaceName: "",
        availableCircuits: ["Monaco Grand Prix"],
      }),
    ).toBe("Monaco Grand Prix");
  });

  it("flags when dashboard data is using the previous season", () => {
    expect(getSeasonDataStatus(2026, 2025)).toEqual({
      hasHistoricalFallback: true,
      requestedYear: 2026,
      dataYear: 2025,
    });

    expect(getSeasonDataStatus(2026, 2026)).toEqual({
      hasHistoricalFallback: false,
      requestedYear: 2026,
      dataYear: 2026,
    });
  });

  it("preserves the existing driver selection when it is already valid", () => {
    const currentSelected = ["NOR", "PIA", "VER"];

    expect(
      getNextSelectedDrivers(currentSelected, ["NOR", "PIA", "VER", "LEC"]),
    ).toBe(currentSelected);
  });

  it("drops invalid driver selections without resetting valid ones", () => {
    expect(
      getNextSelectedDrivers(["NOR", "OLD", "VER"], ["NOR", "VER", "LEC"]),
    ).toEqual(["NOR", "VER"]);
  });

  it("defaults to the first six available drivers when none are valid", () => {
    expect(
      getNextSelectedDrivers(
        ["OLD"],
        ["NOR", "PIA", "VER", "LEC", "HAM", "RUS", "ALO"],
      ),
    ).toEqual(["NOR", "PIA", "VER", "LEC", "HAM", "RUS"]);
  });

  it("declares a favicon asset for the app shell", () => {
    const projectRoot = resolve(__dirname, "../..");
    const html = readFileSync(resolve(projectRoot, "index.html"), "utf8");

    expect(html).toContain('rel="icon"');
    expect(existsSync(resolve(projectRoot, "public/favicon.svg"))).toBe(true);
  });
});
