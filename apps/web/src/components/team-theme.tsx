import type { CSSProperties, ReactNode } from "react";

/** Sets `--team` so `bg-team`, `border-team` etc. take the team colour for everything inside. */
export function TeamTheme({ color, children }: { color: string; children: ReactNode }) {
  return <div style={{ "--team": color } as CSSProperties}>{children}</div>;
}
