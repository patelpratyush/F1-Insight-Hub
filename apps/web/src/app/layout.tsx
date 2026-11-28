import "./globals.css";
import type { Metadata } from "next";
import { AppShell } from "@/components/app-shell";
import { env } from "@/lib/env";

export const metadata: Metadata = {
  title: { default: "F1 Insight Hub", template: "%s · F1 Insight Hub" },
  description: "Live F1 data, telemetry, predictions and fantasy. Unofficial, not affiliated with Formula 1.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell apiBaseUrl={env.API_BASE_URL}>{children}</AppShell>
      </body>
    </html>
  );
}
