import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { DriverStanding } from "@f1/contract";
import { StandingsTable } from "./standings-table";

const row = (over: Partial<DriverStanding> = {}): DriverStanding => ({
  position: 1, points: 423.5, wins: 7, season: 2025, round: 24, updated_at: "2026-10-29T12:00:00Z",
  driver: { id: "d1", code: "NOR", given_name: "Lando", family_name: "Norris", number: 4 },
  team: { id: "t1", name: "McLaren" }, ...over,
});

describe("StandingsTable", () => {
  it("renders fractional points exactly", () => {
    render(<StandingsTable rows={[row()]} />);
    expect(screen.getByText("423.5")).toBeInTheDocument();
  });
  it("renders an empty state", () => {
    render(<StandingsTable rows={[]} />);
    expect(screen.getByText(/no standings/i)).toBeInTheDocument();
  });
  it("falls back to family name when code is missing", () => {
    render(<StandingsTable rows={[row({ driver: { id: "d", code: null, given_name: "A", family_name: "Zed", number: null } })]} />);
    expect(screen.getByText("ZED")).toBeInTheDocument();
  });
});
