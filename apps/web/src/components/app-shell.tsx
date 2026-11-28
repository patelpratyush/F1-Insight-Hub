import type { ReactNode } from "react";
import { CommandPaletteHost } from "./command-palette-host";
import { LeftRail } from "./left-rail";

export function AppShell({ apiBaseUrl, children }: { apiBaseUrl: string; children: ReactNode }) {
  return (
    <div className="md:pl-48">
      <LeftRail />
      <main className="mx-auto max-w-5xl p-6 pb-24 md:pb-6">{children}</main>
      <CommandPaletteHost apiBaseUrl={apiBaseUrl} />
    </div>
  );
}
