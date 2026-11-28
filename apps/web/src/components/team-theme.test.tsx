import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TeamTheme } from "./team-theme";

describe("TeamTheme", () => {
  it("sets the --team css variable", () => {
    const { container } = render(<TeamTheme color="#FF8000"><span>x</span></TeamTheme>);
    expect((container.firstChild as HTMLElement).style.getPropertyValue("--team")).toBe("#FF8000");
  });
});
