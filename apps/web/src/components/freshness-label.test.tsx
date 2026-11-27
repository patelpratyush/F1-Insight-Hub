import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FreshnessLabel } from "./freshness-label";

const now = new Date("2026-10-29T12:00:00Z");

describe("FreshnessLabel", () => {
  it("shows minutes ago", () => {
    render(<FreshnessLabel lastSuccessAt="2026-10-29T11:55:00Z" now={now} />);
    expect(screen.getByText("Updated 5 min ago")).toBeInTheDocument();
  });
  it("warns when stale over 2 hours", () => {
    render(<FreshnessLabel lastSuccessAt="2026-10-29T08:00:00Z" now={now} />);
    expect(screen.getByText(/may be stale/i)).toBeInTheDocument();
  });
  it("handles no data", () => {
    render(<FreshnessLabel lastSuccessAt={null} now={now} />);
    expect(screen.getByText("No data yet")).toBeInTheDocument();
  });
});
