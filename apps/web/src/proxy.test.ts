import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import { config, proxy } from "./proxy";

describe("proxy", () => {
  it("redirects an unauthenticated /standings request to sign-in with next", () => {
    const res = proxy(new NextRequest("http://localhost:3000/standings"));
    expect(res.status).toBe(307);
    const location = new URL(res.headers.get("location") ?? "");
    expect(location.pathname).toBe("/sign-in");
    expect(location.searchParams.get("next")).toBe("/standings");
  });

  it("lets a request with a session cookie through", () => {
    const req = new NextRequest("http://localhost:3000/standings", {
      headers: { cookie: "better-auth.session_token=abc.def" },
    });
    const res = proxy(req);
    expect(res.headers.get("location")).toBeNull();
    expect(res.headers.get("x-middleware-next")).toBe("1");
  });

  it("only guards /standings", () => {
    expect(config.matcher).toEqual(["/standings"]);
  });
});
