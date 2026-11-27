export function safeNext(next: string | null): string {
  const fallback = "/standings";
  if (!next) return fallback;
  if (!next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return fallback;
  return next;
}
