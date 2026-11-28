export function StaleBanner() {
  return (
    <div role="alert" className="rounded border border-timing-yellow/40 bg-timing-yellow/10 px-4 py-2 text-sm text-timing-yellow">
      Live timing has gone quiet. Showing the last update received while we wait for the feed.
    </div>
  );
}
