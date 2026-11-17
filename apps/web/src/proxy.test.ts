import { NextRequest } from "next/server";
import { afterEach, describe, expect, it } from "vitest";
import { config, proxy } from "./proxy";

const original = process.env.API_BASE_URL;
afterEach(() => {
  process.env.API_BASE_URL = original;
});

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

  it("does not require a session outside /standings", () => {
    const res = proxy(new NextRequest("http://localhost:3000/"));
    expect(res.headers.get("location")).toBeNull();
    expect(res.headers.get("x-middleware-next")).toBe("1");
  });

  it("sets CSP from the runtime API_BASE_URL, not a build-time value", () => {
    process.env.API_BASE_URL = "https://api.runtime.example";
    const res = proxy(new NextRequest("http://localhost:3000/"));
    const csp = res.headers.get("content-security-policy") ?? "";
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("connect-src 'self' https://api.runtime.example");
    expect(csp).toContain("frame-ancestors 'none'");
  });

  it("runs on pages but skips static assets", () => {
    const [matcher] = config.matcher;
    expect(matcher).toContain("_next/static");
    expect(new RegExp(`^${matcher}$`).test("/standings")).toBe(true);
    expect(new RegExp(`^${matcher}$`).test("/_next/static/chunk.js")).toBe(false);
  });
});
