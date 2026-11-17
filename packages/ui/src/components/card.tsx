import * as React from "react";
import { cn } from "../lib/cn";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-[var(--radius-card)] border border-carbon-700 bg-carbon-900 p-5", className)}
      {...props}
    />
  );
}
