import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ResultRow } from "@f1/contract";
import { RaceResults } from "./race-results";

const row = (over: Partial<ResultRow> = {}): ResultRow => ({
  position: 1, grid: 2, status: "Finished", points: 25, time_ms: 5400000,
  driver: { id: "d1", ref: "norris", code: "NOR", given_name: "Lando", family_name: "Norris", number: 4 },
  team: { id: "t1", ref: "mclaren", name: "McLaren" }, ...over,
});

describe("RaceResults", () => {
  it("shows DNF status when position is null", () => {
    render(<RaceResults rows={[row({ position: null, status: "Retired", points: 0 })]} />);
    expect(screen.getByText("DNF")).toBeInTheDocument();
    expect(screen.getByText("Retired")).toBeInTheDocument();
  });
  it("shows fractional points", () => {
    render(<RaceResults rows={[row({ points: 0.5 })]} />);
    expect(screen.getByText("0.5")).toBeInTheDocument();
  });
  it("links the driver and the team they drove for", () => {
    render(<RaceResults rows={[row()]} />);
    expect(screen.getByRole("link", { name: "Lando Norris" })).toHaveAttribute("href", "/drivers/norris");
    expect(screen.getByRole("link", { name: "McLaren" })).toHaveAttribute("href", "/teams/mclaren");
  });
  it("renders an empty state when no results", () => {
    render(<RaceResults rows={[]} />);
    expect(screen.getByText("Results not available yet")).toBeInTheDocument();
  });
});
