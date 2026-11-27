import * as React from "react";
import { cn } from "../lib/cn";

export function DataTable({ className, ...props }: React.TableHTMLAttributes<HTMLTableElement>) {
  return <table className={cn("w-full text-left text-sm [&_td]:py-2 [&_th]:py-2 [&_th]:text-carbon-500", className)} {...props} />;
}
