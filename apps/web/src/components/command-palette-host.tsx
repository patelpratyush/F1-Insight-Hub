"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { createApiClient, type SearchHit } from "@f1/contract";
import { CommandPalette } from "@f1/ui";

/** Cmd/Ctrl+K palette fed by `/v1/search`, debounced 150 ms. The browser calls the API
 *  directly (CORS and CSP connect-src already allow API_BASE_URL) so rate limits apply per viewer. */
export function CommandPaletteHost({ apiBaseUrl }: { apiBaseUrl: string }) {
  const router = useRouter();
  const api = useMemo(() => createApiClient(apiBaseUrl), [apiBaseUrl]);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) return; // the API rejects shorter queries
    let stale = false;
    const id = setTimeout(async () => {
      const { data } = await api
        .GET("/v1/search", { params: { query: { q: q.slice(0, 64) } } })
        .catch(() => ({ data: undefined }));
      if (!stale) setHits(data ?? []);
    }, 150);
    return () => {
      stale = true;
      clearTimeout(id);
    };
  }, [api, query]);

  const shown = query.trim().length < 2 ? [] : hits;
  return (
    <CommandPalette
      items={shown.map((h) => ({ id: h.id, label: h.label, hint: h.hint ?? h.kind }))}
      onQueryChange={setQuery}
      onSelect={(item) => {
        const hit = shown.find((h) => h.id === item.id);
        if (hit) router.push(hit.href);
      }}
    />
  );
}
