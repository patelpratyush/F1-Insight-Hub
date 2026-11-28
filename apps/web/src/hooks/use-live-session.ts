"use client";

import type { LiveState } from "@f1/contract";
import { useEffect, useState } from "react";

/** The slice of the browser EventSource this hook uses; tests pass a fake. */
export interface EventSourceLike {
  readonly readyState: number;
  addEventListener(type: string, listener: (e: MessageEvent) => void): void;
  close(): void;
}

export type LiveConnection = "connecting" | "live" | "reconnecting" | "stale";

const CLOSED = 2; // EventSource.CLOSED
const STALE_MS = 20_000;
const MAX_BACKOFF_MS = 15_000;

const browserEventSource = (url: string): EventSourceLike => new EventSource(url);

export function useLiveSession(
  sessionKey: number,
  opts?: { eventSourceFactory?: (url: string) => EventSourceLike; now?: () => number; baseUrl?: string },
) {
  const { eventSourceFactory = browserEventSource, now = Date.now, baseUrl = "" } = opts ?? {};
  const [state, setState] = useState<LiveState | null>(null);
  const [connection, setConnection] = useState<LiveConnection>("connecting");
  const [lastEventAt, setLastEventAt] = useState<number | null>(null);

  useEffect(() => {
    const url = `${baseUrl}/v1/live/${sessionKey}/stream`;
    let es: EventSourceLike | null = null;
    let attempt = 0;
    let status: LiveState["status"] | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let staleTimer: ReturnType<typeof setTimeout> | undefined;

    // Heartbeats are SSE comments, which EventSource never surfaces to JS, so only `tower`
    // events count as activity. A waiting/finished stream legitimately sends nothing but
    // heartbeats, so staleness is only judged while live (or before any event arrived).
    const armStale = () => {
      clearTimeout(staleTimer);
      staleTimer = setTimeout(() => {
        if (status === null || status === "live") setConnection("stale");
      }, STALE_MS);
    };

    const connect = () => {
      const source = eventSourceFactory(url); // the browser resends Last-Event-ID on its own retries
      es = source;
      armStale();
      source.addEventListener("tower", (e) => {
        const next = JSON.parse(e.data) as LiveState;
        status = next.status;
        attempt = 0;
        setState(next);
        setLastEventAt(now());
        setConnection("live");
        armStale();
      });
      source.addEventListener("error", () => {
        setConnection("reconnecting");
        if (source.readyState !== CLOSED) return; // the browser is retrying by itself
        // shortcut: a manual reconnect is a new EventSource, so Last-Event-ID is not sent and
        // the server replies with its current snapshot; fine because every event is a full state.
        source.close();
        clearTimeout(staleTimer);
        retryTimer = setTimeout(connect, Math.min(1000 * 2 ** attempt, MAX_BACKOFF_MS));
        attempt += 1;
      });
    };

    connect();
    return () => {
      clearTimeout(retryTimer);
      clearTimeout(staleTimer);
      es?.close();
    };
  }, [sessionKey, baseUrl, eventSourceFactory, now]);

  return { state, connection, lastEventAt };
}
