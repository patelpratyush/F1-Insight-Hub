import { getSessionCookie } from "better-auth/cookies";
import { NextResponse, type NextRequest } from "next/server";

const PROTECTED = ["/standings"];

// Built per request so API_BASE_URL is read at runtime, not baked in at build time.
function contentSecurityPolicy(): string {
  const api = process.env.API_BASE_URL ?? "http://localhost:8000";
  return [
    "default-src 'self'",
    "img-src 'self' data: https:",
    "style-src 'self' 'unsafe-inline'",
    "script-src 'self' 'unsafe-inline'",
    `connect-src 'self' ${api}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const needsSession = PROTECTED.some((p) => pathname === p || pathname.startsWith(`${p}/`));
  let response: NextResponse;
  if (needsSession && !getSessionCookie(request)) {
    const signIn = new URL("/sign-in", request.url);
    signIn.searchParams.set("next", pathname);
    response = NextResponse.redirect(signIn);
  } else {
    response = NextResponse.next();
  }
  response.headers.set("Content-Security-Policy", contentSecurityPolicy());
  return response;
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
