"use client";
import { useSyncExternalStore } from "react";
import { formatLocalDateTime } from "@/lib/format";

const noop = () => () => {};

/** The API returns UTC. The server cannot know the viewer's zone, so it renders UTC and the
 *  browser swaps in local time after hydration (no mismatch warning). */
export function LocalTime({ iso }: { iso: string }) {
  const text = useSyncExternalStore(
    noop,
    () => formatLocalDateTime(iso),
    () => `${formatLocalDateTime(iso, "en-GB", "UTC")} UTC`,
  );
  return <time dateTime={iso}>{text}</time>;
}
