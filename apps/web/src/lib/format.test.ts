import { describe, expect, it } from "vitest";
import { formatGap, formatLapTime, formatLocalDateTime } from "./format";

describe("formatLapTime", () => {
  it("formats minutes, seconds, millis", () => expect(formatLapTime(81456)).toBe("1:21.456"));
  it("pads seconds", () => expect(formatLapTime(60005)).toBe("1:00.005"));
  it("handles sub-minute", () => expect(formatLapTime(59999)).toBe("59.999"));
  it("returns dash for null", () => expect(formatLapTime(null)).toBe("—"));
});
describe("formatGap", () => {
  it("keeps lap gaps verbatim", () => expect(formatGap("+1 LAP")).toBe("+1 LAP"));
  it("dashes null", () => expect(formatGap(null)).toBe("—"));
  it("dashes empty", () => expect(formatGap("")).toBe("—"));
});
describe("formatLocalDateTime", () => {
  it("converts UTC to the given timezone", () =>
    expect(formatLocalDateTime("2025-03-16T04:00:00Z", "en-GB", "Australia/Melbourne")).toContain("15:00"));
  it("uses a different zone for the same instant", () =>
    expect(formatLocalDateTime("2025-03-16T04:00:00Z", "en-GB", "Europe/London")).toContain("04:00"));
});
