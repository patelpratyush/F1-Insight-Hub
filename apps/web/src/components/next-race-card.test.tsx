import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { RaceSummary } from "@f1/contract";
import { pickNextRace } from "@/lib/next-race";
import { NextRaceCard } from "./next-race-card";

const race = (round: number, sessions: RaceSummary["sessions"]): RaceSummary => ({
  season: 2025, round, name: `GP ${round}`, race_date: "2025-03-16", circuit: null, sessions,
});
const NOW = new Date("2025-03-12T00:00:00Z");

describe("NextRaceCard", () => {
  it("counts down to the next session", () => {
    const r = race(1, [{ type: "FP1", starts_at: "2025-03-14T03:00:00Z", status: "scheduled" }]);
    render(<NextRaceCard race={r} now={NOW} />);
    expect(screen.getByText(/Starts in 2d 3h/)).toBeInTheDocument();
  });
  it("shows live now when a session is live", () => {
    const r = race(1, [{ type: "R", starts_at: "2025-03-11T23:00:00Z", status: "live" }]);
    render(<NextRaceCard race={r} now={NOW} />);
    expect(screen.getByText("Live now")).toBeInTheDocument();
  });
  it("links to the live race centre when the live session has an OpenF1 key", () => {
    const r = race(1, [{ type: "R", starts_at: "2025-03-11T23:00:00Z", status: "live", openf1_session_key: 9158 }]);
    render(<NextRaceCard race={r} now={NOW} />);
    expect(screen.getByRole("link", { name: /Watch live/ })).toHaveAttribute("href", "/live/9158");
  });
  it("ignores cancelled sessions and shows season complete when nothing is ahead", () => {
    const r = race(1, [
      { type: "R", starts_at: "2025-03-10T04:00:00Z", status: "finished" },
      { type: "SPRINT", starts_at: "2025-03-20T04:00:00Z", status: "cancelled" },
    ]);
    render(<NextRaceCard race={r} now={NOW} />);
    expect(screen.getByText("Season complete")).toBeInTheDocument();
  });
  it("renders an empty state without a race", () => {
    render(<NextRaceCard race={null} now={NOW} />);
    expect(screen.getByText(/No races scheduled/)).toBeInTheDocument();
  });
});

describe("pickNextRace", () => {
  const past = race(1, [{ type: "R", starts_at: "2025-03-10T04:00:00Z", status: "finished" }]);
  const next = race(2, [{ type: "R", starts_at: "2025-03-20T04:00:00Z", status: "scheduled" }]);
  it("picks the first race with a session ahead", () => expect(pickNextRace([past, next], NOW)).toBe(next));
  it("falls back to the last race", () => expect(pickNextRace([past], NOW)).toBe(past));
  it("returns null for no races", () => expect(pickNextRace([], NOW)).toBeNull());
});
