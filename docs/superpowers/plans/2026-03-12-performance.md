# Performance Optimization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate duplicate API URL strings, add React Query caching to Dashboard, and lazy-load route pages to cut the initial JS bundle.

**Architecture:**
- A single `src/lib/api.ts` constant replaces 10+ scattered `import.meta.env.VITE_API_URL || "http://localhost:8000"` strings.
- Dashboard's 7 `useApiCall` hooks are migrated to `useQuery` (same pattern already applied to TelemetryAnalyzer), giving automatic caching and deduplication.
- `React.lazy()` wraps all page imports in `App.tsx` so only the landing page code loads on initial visit; each route chunk loads on navigation.

**Tech Stack:** React 18, @tanstack/react-query v5, Vite, TypeScript

---

## Chunk 1: Shared API URL constant

### Task 1: Create src/lib/api.ts

**Files:**
- Create: `src/lib/api.ts`
- Modify: `src/pages/Dashboard.tsx`
- Modify: `src/pages/TelemetryAnalyzer.tsx`
- Modify: `src/hooks/useF1Metadata.ts`
- Modify: `src/components/WeatherContextPanel.tsx`

- [ ] **Step 1: Search for all occurrences to confirm scope**

```bash
grep -rn 'VITE_API_URL' /Users/pratyush/F1-Insight-Hub/src --include="*.ts" --include="*.tsx"
```
Note every file path returned — those are all the files to update.

- [ ] **Step 2: Create the shared constant file**

Create `src/lib/api.ts`:
```typescript
export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
```

That's the entire file.

- [ ] **Step 3: Replace all occurrences in src/**

For every file from Step 1, replace:
```typescript
// OLD
const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
```
With:
```typescript
// NEW
import { API_BASE } from "@/lib/api";
// then use API_BASE instead of apiUrl
```

Example diff in `src/hooks/useF1Metadata.ts`:
```typescript
// Before
const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
const response = await fetch(`${apiUrl}/api/metadata/drivers/${year}`);

// After
import { API_BASE } from "@/lib/api";
const response = await fetch(`${API_BASE}/api/metadata/drivers/${year}`);
```

- [ ] **Step 4: Verify no remaining raw occurrences**

```bash
grep -rn 'VITE_API_URL' /Users/pratyush/F1-Insight-Hub/src --include="*.ts" --include="*.tsx"
```
Expected: no output

- [ ] **Step 5: Start the dev server and check the app loads**

```bash
cd /Users/pratyush/F1-Insight-Hub && npm run dev
```
Open http://localhost:5173 — Dashboard and Telemetry should work normally.

- [ ] **Step 6: Commit**

```bash
git add src/lib/api.ts src/pages/Dashboard.tsx src/pages/TelemetryAnalyzer.tsx \
        src/hooks/useF1Metadata.ts src/components/WeatherContextPanel.tsx
git commit -m "refactor: centralize API base URL in src/lib/api.ts"
```

---

## Chunk 2: Dashboard useQuery migration

### Task 2: Migrate Dashboard static queries to useQuery

The Dashboard has 6 API calls that load once on mount and never depend on changing state (except `liveWeatherApi` which depends on `selectedCircuit`). These should use `useQuery` for caching. Currently they use `useApiCall` which has no cache — every page visit re-fetches everything.

**Files:**
- Modify: `src/pages/Dashboard.tsx:74-206`

- [ ] **Step 1: Add useQuery import to Dashboard.tsx**

At the top of `src/pages/Dashboard.tsx`, the `useApiCall` import is on line 17. Add `useQuery` import alongside existing react-query import (or add it if missing):

```typescript
import { useQuery } from "@tanstack/react-query";
import { API_BASE } from "@/lib/api";
```

Remove the `useApiCall` import from Dashboard.tsx (line 17) once all calls are migrated.

- [ ] **Step 2: Migrate dashboardApi**

Replace lines 74-87:
```typescript
// REMOVE
const dashboardApi = useApiCall(async () => { ... }, { maxRetries: 3, ... });

// ADD
const { data: dashboardData, isLoading: dashboardLoading, error: dashboardError } = useQuery({
  queryKey: ["dashboard", seasonYear],
  queryFn: async () => {
    const response = await fetch(`${API_BASE}/api/f1/dashboard/${seasonYear}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error(data.message || "Failed to fetch dashboard data");
    return data.data;
  },
  staleTime: 1000 * 60 * 5, // 5 min — dashboard data changes only between races
  retry: 3,
});
```

Note: The current `dashboardApi` also calls `setDataYear(data.data_year)`. Move that side-effect to a `useEffect` watching `dashboardData`:
```typescript
useEffect(() => {
  if (dashboardData?.data_year) setDataYear(dashboardData.data_year);
}, [dashboardData]);
```

- [ ] **Step 3: Migrate performanceTrendsLast5Api**

Replace lines 89-103:
```typescript
const { data: trendsLast5, isLoading: trendsLast5Loading } = useQuery({
  queryKey: ["dashboard-trends", seasonYear, "last5"],
  queryFn: async () => {
    const response = await fetch(`${API_BASE}/api/f1/dashboard-trends/${seasonYear}?all_races=false`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error(data.message || "Failed to fetch performance trends");
    return data.performance_trends;
  },
  staleTime: 1000 * 60 * 5,
  retry: 3,
});
```

- [ ] **Step 4: Migrate performanceTrendsAllApi**

Replace lines 105-119:
```typescript
const { data: trendsAll, isLoading: trendsAllLoading } = useQuery({
  queryKey: ["dashboard-trends", seasonYear, "all"],
  queryFn: async () => {
    const response = await fetch(`${API_BASE}/api/f1/dashboard-trends/${seasonYear}?all_races=true`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error(data.message || "Failed to fetch performance trends");
    return data.performance_trends;
  },
  staleTime: 1000 * 60 * 5,
  retry: 3,
});
```

- [ ] **Step 5: Migrate liveChampionshipApi**

Replace lines 138-150:
```typescript
const { data: championshipData, isLoading: championshipLoading } = useQuery({
  queryKey: ["championship-standings"],
  queryFn: async () => {
    const response = await fetch(`${API_BASE}/api/championship/standings`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error("Failed to fetch championship standings");
    return data;
  },
  staleTime: 1000 * 60 * 10, // standings update ~hourly
  retry: 2,
  refetchInterval: 1000 * 60 * 10, // auto-refresh every 10 min
});
```

- [ ] **Step 6: Migrate availableCircuitsApi**

Replace lines 152-163:
```typescript
const { data: availableCircuits } = useQuery({
  queryKey: ["weather-circuits"],
  queryFn: async () => {
    const response = await fetch(`${API_BASE}/api/weather/circuits`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error("Failed to fetch available circuits");
    return data.circuits;
  },
  staleTime: 1000 * 60 * 60, // circuit list rarely changes
  retry: 2,
});
```

- [ ] **Step 7: Migrate nextRaceApi**

Replace lines 165-176:
```typescript
const { data: nextRaceData } = useQuery({
  queryKey: ["next-race", seasonYear],
  queryFn: async () => {
    const response = await fetch(`${API_BASE}/api/results/next-race?year=${seasonYear}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error("Failed to fetch next race");
    return data;
  },
  staleTime: 1000 * 60 * 60,
  retry: 2,
});
```

- [ ] **Step 8: Migrate liveWeatherApi (depends on selectedCircuit)**

Replace lines 121-136:
```typescript
const { data: liveWeatherData, isLoading: weatherLoading } = useQuery({
  queryKey: ["live-weather", selectedCircuit],
  queryFn: async () => {
    const response = await fetch(`${API_BASE}/api/weather/current`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ circuit_name: selectedCircuit }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error("Failed to fetch weather data");
    return data;
  },
  enabled: !!selectedCircuit,  // only fetches when a circuit is selected
  staleTime: 1000 * 60 * 5,
  retry: 2,
});
```

- [ ] **Step 9: Update all JSX references**

Search the Dashboard JSX for `dashboardApi.data`, `performanceTrendsLast5Api.data`, etc. and replace with the new variable names:

| Old | New |
|-----|-----|
| `dashboardApi.data` | `dashboardData` |
| `dashboardApi.loading` | `dashboardLoading` |
| `performanceTrendsLast5Api.data` | `trendsLast5` |
| `performanceTrendsAllApi.data` | `trendsAll` |
| `liveWeatherApi.data` | `liveWeatherData` |
| `liveWeatherApi.loading` | `weatherLoading` |
| `liveChampionshipApi.data` | `championshipData` |
| `availableCircuitsApi.data` | `availableCircuits` |
| `nextRaceApi.data` | `nextRaceData` |

- [ ] **Step 10: Remove useApiCall import (if no longer used in Dashboard)**

```bash
grep -n 'useApiCall' src/pages/Dashboard.tsx
```
If no occurrences remain, remove the import line.

- [ ] **Step 11: Verify Dashboard renders correctly**

```bash
npm run dev
```
Open http://localhost:5173/dashboard. All panels should populate. Navigate away and back — data loads instantly from cache (no loading spinners on second visit).

- [ ] **Step 12: Commit**

```bash
git add src/pages/Dashboard.tsx src/lib/api.ts
git commit -m "perf: migrate Dashboard API calls from useApiCall to useQuery with caching"
```

---

## Chunk 3: Route-level code splitting

### Task 3: Lazy-load page routes in App.tsx

**Files:**
- Modify: `src/App.tsx`

- [ ] **Step 1: Measure current bundle size as baseline**

```bash
cd /Users/pratyush/F1-Insight-Hub && npm run build 2>&1 | grep "dist/assets"
```
Note the sizes of the `.js` chunks.

- [ ] **Step 2: Convert all page imports to React.lazy**

Open `src/App.tsx`. Replace lines 8-13 (the eager page imports):

```typescript
// REMOVE these
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import DriverPredictor from "./pages/DriverPredictor";
import RacePredictor from "./pages/RacePredictor";
import TelemetryAnalyzer from "./pages/TelemetryAnalyzer";
import StrategySimulator from "./pages/StrategySimulator";
import NotFound from "./pages/NotFound";

// ADD these
import { lazy, Suspense } from "react";
const Index = lazy(() => import("./pages/Index"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const DriverPredictor = lazy(() => import("./pages/DriverPredictor"));
const RacePredictor = lazy(() => import("./pages/RacePredictor"));
const TelemetryAnalyzer = lazy(() => import("./pages/TelemetryAnalyzer"));
const StrategySimulator = lazy(() => import("./pages/StrategySimulator"));
const NotFound = lazy(() => import("./pages/NotFound"));
```

- [ ] **Step 3: Wrap Routes in Suspense**

In the JSX, wrap `<Routes>` with `<Suspense>`:

```tsx
<Layout>
  <Suspense fallback={
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
    </div>
  }>
    <Routes>
      <Route path="/" element={<Index />} />
      {/* ... rest of routes unchanged */}
    </Routes>
  </Suspense>
</Layout>
```

- [ ] **Step 4: Build and compare bundle sizes**

```bash
npm run build 2>&1 | grep "dist/assets"
```
Expected: The main chunk should be noticeably smaller. There should now be multiple smaller chunks (one per page route) instead of one large bundle.

- [ ] **Step 5: Verify navigation still works**

```bash
npm run preview
```
Open http://localhost:4173. Navigate between all pages. Each should load (brief spinner on first visit, instant on return).

- [ ] **Step 6: Commit**

```bash
git add src/App.tsx
git commit -m "perf: lazy-load all page routes to reduce initial bundle size"
```
