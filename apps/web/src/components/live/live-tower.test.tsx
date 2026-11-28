import type { DriverTiming } from "@f1/contract";
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LiveTower } from "./live-tower";

function driver(number: number, over: Partial<DriverTiming> = {}): DriverTiming {
  return {
    number,
    position: number,
    code: `D${number}`,
    last_lap_ms: null,
    best_lap_ms: null,
    best_sectors_ms: [null, null, null],
    gap_to_leader: null,
    interval: null,
    compound: "SOFT",
    tyre_age_laps: 3,
    in_pit: false,
    retired: false,
    sectors: ["purple", "green", "yellow"],
    ...over,
  };
}

describe("LiveTower", () => {
  it("renders PIT chip for drivers in the pit lane", () => {
    render(<LiveTower status="live" rows={[driver(1), driver(2, { in_pit: true })]} />);
    const rows = screen.getAllByRole("row");
    expect(within(rows[1]!).getByText("PIT")).toBeInTheDocument();
    expect(within(rows[0]!).queryByText("PIT")).not.toBeInTheDocument();
    expect(rows.map((r) => r.getAttribute("aria-label")?.split(" ")[1])).toEqual(["D1", "D2"]);
  });

  it("renders OUT for retired drivers and sorts them last", () => {
    const rows = [driver(1), driver(2, { retired: true, position: null }), driver(3)];
    render(<LiveTower status="live" rows={rows} />);
    const rendered = screen.getAllByRole("row");
    expect(rendered.map((r) => r.getAttribute("aria-label")?.split(" ")[1])).toEqual(["D1", "D3", "D2"]);
    expect(within(rendered[2]!).getByText("OUT")).toBeInTheDocument();
  });

  it("renders verbatim lap gaps like +1 LAP", () => {
    const rows = [driver(1), driver(2, { gap_to_leader: "+1 LAP", interval: "+0.512" }), driver(3, { gap_to_leader: null })];
    render(<LiveTower status="live" rows={rows} />);
    expect(screen.getByText("+1 LAP")).toBeInTheDocument();
    expect(screen.getByText("+0.512")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("NaN");
  });

  it("shows 'Waiting for live data' instead of an empty tower when waiting", () => {
    render(<LiveTower status="waiting" rows={[]} />);
    expect(screen.getByText("Waiting for live data")).toBeInTheDocument();
    expect(screen.queryAllByRole("row")).toHaveLength(0);
  });
});
