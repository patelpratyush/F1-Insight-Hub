"use client";

import type { DriverTiming, LiveState } from "@f1/contract";
import { TimingTowerRow } from "@f1/ui";
import { useLayoutEffect, useRef } from "react";
import { formatGap } from "@/lib/format";

/** FLIP: rows that changed place start at their old offset and slide to the new one. */
function useFlip(order: string) {
  const container = useRef<HTMLDivElement>(null);
  const tops = useRef(new Map<string, number>());
  useLayoutEffect(() => {
    const el = container.current;
    if (!el) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    const next = new Map<string, number>();
    for (const row of el.querySelectorAll<HTMLElement>("[data-flip-key]")) {
      const key = row.dataset.flipKey!;
      const top = row.getBoundingClientRect().top;
      next.set(key, top);
      const prev = tops.current.get(key);
      if (reduce || prev === undefined || prev === top) continue;
      row.style.transition = "none";
      row.style.transform = `translateY(${prev - top}px)`;
      void row.offsetHeight; // commit the inverted position before animating back
      row.style.transition = "transform 300ms ease";
      row.style.transform = "";
    }
    tops.current = next;
  }, [order]);
  return container;
}

export function LiveTower({ rows, status }: { rows: DriverTiming[]; status: LiveState["status"] | null }) {
  // Server order is tower order; only push retired cars to the bottom (sort is stable).
  const ordered = [...rows].sort((a, b) => Number(a.retired) - Number(b.retired));
  const container = useFlip(ordered.map((d) => d.number).join(","));

  if (ordered.length === 0) {
    return (
      <div role="status" className="rounded-[var(--radius-card)] border border-carbon-800 bg-carbon-900 px-6 py-12 text-center">
        <p className="font-[var(--font-display)] text-2xl font-bold">
          {status === "finished" ? "Session finished" : "Waiting for live data"}
        </p>
        <p className="mt-2 text-sm text-carbon-500">
          {status === "finished"
            ? "No timing data was recorded for this session."
            : "The tower fills in as soon as the session starts sending timing. This page updates on its own."}
        </p>
      </div>
    );
  }

  return (
    <div ref={container} role="table" aria-label="Live timing tower">
      {ordered.map((d) => {
        const chip = d.retired ? "OUT" : d.in_pit ? "PIT" : null;
        return (
          <div key={d.number} data-flip-key={d.number}>
            <TimingTowerRow
              position={d.position}
              code={d.code ?? String(d.number)}
              name={`#${d.number}`}
              value={formatGap(d.gap_to_leader)}
              delta={formatGap(d.interval)}
              sectors={d.sectors}
              compound={d.compound}
              {...(chip && { chip })}
            />
          </div>
        );
      })}
    </div>
  );
}
