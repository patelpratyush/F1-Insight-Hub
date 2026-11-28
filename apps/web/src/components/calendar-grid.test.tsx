import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SessionList } from "./calendar-grid";

describe("SessionList", () => {
  it("links a live session to the live race centre", () => {
    render(<SessionList sessions={[{ type: "R", starts_at: "2025-03-16T04:00:00Z", status: "live", openf1_session_key: 9158 }]} />);
    expect(screen.getByRole("link", { name: /Watch live/ })).toHaveAttribute("href", "/live/9158");
  });
  it("shows live without a link until the OpenF1 key is known", () => {
    render(<SessionList sessions={[{ type: "R", starts_at: "2025-03-16T04:00:00Z", status: "live", openf1_session_key: null }]} />);
    expect(screen.getByText("live")).toBeInTheDocument();
    expect(screen.queryByRole("link")).toBeNull();
  });
  it("does not link finished sessions", () => {
    render(<SessionList sessions={[{ type: "R", starts_at: "2025-03-16T04:00:00Z", status: "finished", openf1_session_key: 9158 }]} />);
    expect(screen.queryByRole("link")).toBeNull();
  });
});
