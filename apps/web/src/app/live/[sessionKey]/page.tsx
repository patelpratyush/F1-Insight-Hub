import { notFound } from "next/navigation";
import { LiveView } from "@/components/live/live-view";

export default async function LivePage({ params }: { params: Promise<{ sessionKey: string }> }) {
  const { sessionKey } = await params;
  if (!/^\d{1,9}$/.test(sessionKey)) notFound();
  const key = Number(sessionKey);
  // The browser streams straight from the API. Same source and default as the CSP connect-src
  // in proxy.ts, read per request (not lib/env, which also demands the auth secrets).
  const api = (process.env.API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
  return <LiveView key={key} sessionKey={key} apiBaseUrl={api} />;
}
