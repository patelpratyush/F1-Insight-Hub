import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TimingTowerRow } from "./timing-tower-row";

describe("TimingTowerRow", () => {
  it("shows position, code, and value in an accessible row", () => {
    render(<TimingTowerRow position={1} code="NOR" name="Lando Norris" value="423.5" />);
    const row = screen.getByRole("row", { name: /1 NOR Lando Norris 423.5/ });
    expect(row).toBeInTheDocument();
  });

  it("applies the purple sector class", () => {
    render(<TimingTowerRow position={2} code="VER" name="Max Verstappen" value="1:21.3" sector="purple" />);
    expect(screen.getByTestId("sector-bar")).toHaveClass("bg-timing-purple");
  });

  it("renders fractional values verbatim", () => {
    render(<TimingTowerRow position={3} code="PIA" name="Oscar Piastri" value="12.5" />);
    expect(screen.getByText("12.5")).toBeInTheDocument();
  });
});
