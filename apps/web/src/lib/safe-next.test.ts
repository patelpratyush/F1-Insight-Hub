import { describe, expect, it } from "vitest";
import { safeNext } from "./safe-next";

describe("safeNext", () => {
  it("allows same-origin paths", () => expect(safeNext("/standings")).toBe("/standings"));
  it("falls back for null", () => expect(safeNext(null)).toBe("/standings"));
  it.each(["https://evil.com", "//evil.com", "/\\evil.com", "javascript:alert(1)"])(
    "rejects %s", (bad) => expect(safeNext(bad)).toBe("/standings"),
  );
});
