"use client";

import { useLiveSession } from "@/hooks/use-live-session";
import { FlagBanner } from "./flag-banner";
import { LiveHeader } from "./live-header";
import { LiveTower } from "./live-tower";
import { StaleBanner } from "./stale-banner";
import { WeatherPanel } from "./weather-panel";

export function LiveView({ sessionKey, apiBaseUrl }: { sessionKey: number; apiBaseUrl: string }) {
  const { state, connection, lastEventAt } = useLiveSession(sessionKey, { baseUrl: apiBaseUrl });
  return (
    <section className="space-y-4">
      <LiveHeader state={state} connection={connection} lastEventAt={lastEventAt} />
      {connection === "stale" ? <StaleBanner /> : null}
      {state ? <FlagBanner flag={state.flag} /> : null}
      <WeatherPanel weather={null} />
      <LiveTower rows={state?.drivers ?? []} status={state?.status ?? null} />
    </section>
  );
}
