import Link from "next/link";

// Add entries here as sections ship (e.g. Live).
export const NAV: { href: string; label: string; prefetch?: false }[] = [
  { href: "/", label: "Home" },
  { href: "/calendar", label: "Calendar" },
  // Auth-gated: a prefetch while signed out caches the sign-in redirect, which then wins after sign-in.
  { href: "/standings", label: "Standings", prefetch: false },
];

/** Left rail on desktop; the same nav pins to the bottom of the screen on mobile. */
export function LeftRail() {
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-10 flex justify-around border-t border-carbon-700 bg-carbon-900 md:inset-y-0 md:left-0 md:right-auto md:w-48 md:flex-col md:justify-start md:gap-1 md:border-r md:border-t-0 md:p-4"
    >
      <Link href="/" className="hidden px-3 pb-6 font-[var(--font-display)] text-xl font-extrabold tracking-wide md:block">
        F1 INSIGHT HUB
      </Link>
      {NAV.map((n) => (
        <Link key={n.href} href={n.href} prefetch={n.prefetch ?? null} className="px-3 py-3 text-sm text-carbon-200 hover:text-white md:rounded md:py-2 md:hover:bg-carbon-800">
          {n.label}
        </Link>
      ))}
      <span className="hidden px-3 pt-6 text-xs text-carbon-500 md:block">Search: Ctrl/⌘ K</span>
    </nav>
  );
}
