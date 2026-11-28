"use client";

import type { LiveState } from "@f1/contract";
import { useEffect, useState } from "react";
import type { LiveConnection } from "@/hooks/use-live-session";

const connectionLabel: Record<LiveConnection, string> = {
  connecting: "Connecting",
  live: "Connected",
  reconnecting: "Reconnecting",
  stale: "Stale",
};

export function LiveHeader({
  state,
  connection,
  lastEventAt,
}: {
  state: LiveState | null;
  connection: LiveConnection;
  lastEventAt: number | null;
}) {
  const [clock, setClock] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const ago = lastEventAt === null ? null : Math.max(0, Math.round((clock - lastEventAt) / 1000));
  return (
    <header className="space-y-1">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <h1 className="font-[var(--font-display)] text-4xl font-bold">Live Race Centre</h1>
        <p className="text-sm text-carbon-500">
          {state?.lap != null ? <span className="tabular mr-3 text-carbon-200">Lap {state.lap}</span> : null}
          {connectionLabel[connection]} · {ago === null ? "No update received yet" : `Updated ${ago}s ago`}
        </p>
      </div>
      <p className="text-xs text-carbon-500">Unofficial, community data (OpenF1). Not affiliated with Formula 1.</p>
    </header>
  );
}
