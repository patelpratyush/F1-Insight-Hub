import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SeasonNote } from "./season-note";

describe("SeasonNote", () => {
  it("explains a fallback to an earlier season", () => {
    render(<SeasonNote shownSeason={2025} requestedSeason={null} currentYear={2026} />);
    expect(screen.getByText("Showing 2025 standings. The 2026 season has no results yet.")).toBeInTheDocument();
  });
  it("renders nothing for the current season", () => {
    const { container } = render(<SeasonNote shownSeason={2026} requestedSeason={null} currentYear={2026} />);
    expect(container).toBeEmptyDOMElement();
  });
  it("renders nothing when a season was explicitly requested", () => {
    const { container } = render(<SeasonNote shownSeason={2019} requestedSeason={2019} currentYear={2026} />);
    expect(container).toBeEmptyDOMElement();
  });
  it("renders nothing without data", () => {
    const { container } = render(<SeasonNote shownSeason={null} requestedSeason={null} currentYear={2026} />);
    expect(container).toBeEmptyDOMElement();
  });
});
