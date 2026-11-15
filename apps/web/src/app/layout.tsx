import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "F1 Insight Hub",
  description: "Live F1 data, telemetry, predictions and fantasy. Unofficial, not affiliated with Formula 1.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="mx-auto max-w-4xl p-6">{children}</main>
      </body>
    </html>
  );
}
