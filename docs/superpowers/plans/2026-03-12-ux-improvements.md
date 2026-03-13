# UX Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an app-wide error boundary, persist user selections across page refreshes, and add a live auto-refresh for championship standings.

**Architecture:**
- A `src/components/ErrorBoundary.tsx` class component wraps each route so one page crashing doesn't take down the whole app.
- A `src/hooks/usePersistedState.ts` hook wraps `useState` with `localStorage` sync — drop-in replacement for any selector state you want to survive a page refresh.
- Championship standings gain a `refetchInterval` (already added in the performance plan) plus a visible "last updated" timestamp.

**Tech Stack:** React 18, TypeScript, localStorage API, @tanstack/react-query

---

## Chunk 1: Error Boundary

### Task 1: Create ErrorBoundary component

React error boundaries must be class components — hooks can't catch render errors.

**Files:**
- Create: `src/components/ErrorBoundary.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: Create the component**

Create `src/components/ErrorBoundary.tsx`:
```tsx
import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="text-6xl mb-6">⚠️</div>
            <h2 className="text-2xl font-bold text-white mb-3">Something went wrong</h2>
            <p className="text-gray-400 mb-6 text-sm font-mono">
              {this.state.error?.message}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-full font-bold"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
```

- [ ] **Step 2: Wrap each route with ErrorBoundary in App.tsx**

In `src/App.tsx`, import ErrorBoundary and wrap the `element` prop of each route:

```tsx
import { ErrorBoundary } from "./components/ErrorBoundary";

// In Routes:
<Route path="/dashboard" element={
  <ErrorBoundary>
    <Dashboard />
  </ErrorBoundary>
} />
<Route path="/telemetry" element={
  <ErrorBoundary>
    <TelemetryAnalyzer />
  </ErrorBoundary>
} />
// ... same pattern for all routes
```

- [ ] **Step 3: Manually verify the boundary catches errors**

Temporarily add a throw to `Dashboard.tsx` at the top of the component:
```tsx
throw new Error("Test error boundary");
```
Open http://localhost:5173/dashboard — you should see the error UI, not a blank white screen. The nav and other routes should still work.

Remove the test throw after verifying.

- [ ] **Step 4: Commit**

```bash
git add src/components/ErrorBoundary.tsx src/App.tsx
git commit -m "feat: add ErrorBoundary to all routes to prevent full-app crashes"
```

---

## Chunk 2: Persistent user selections

### Task 2: Create usePersistedState hook

**Files:**
- Create: `src/hooks/usePersistedState.ts`
- Modify: `src/pages/TelemetryAnalyzer.tsx`
- Modify: `src/pages/Dashboard.tsx`

- [ ] **Step 1: Create the hook**

Create `src/hooks/usePersistedState.ts`:
```typescript
import { useState, useEffect } from "react";

export function usePersistedState<T>(
  key: string,
  defaultValue: T,
): [T, React.Dispatch<React.SetStateAction<T>>] {
  const [state, setState] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored !== null ? (JSON.parse(stored) as T) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(state));
    } catch {
      // localStorage full or unavailable — fail silently
    }
  }, [key, state]);

  return [state, setState];
}
```

- [ ] **Step 2: Use the hook in TelemetryAnalyzer for race/session/driver**

Open `src/pages/TelemetryAnalyzer.tsx`. Find these `useState` lines:
```typescript
const [selectedSeason, setSelectedSeason] = useState(String(currentYear));
const [selectedGP, setSelectedGP] = useState("");
const [selectedSession, setSelectedSession] = useState("Qualifying");
const [selectedDriver, setSelectedDriver] = useState("");
const [selectedDriver2, setSelectedDriver2] = useState("");
```

Replace with:
```typescript
import { usePersistedState } from "@/hooks/usePersistedState";

const [selectedSeason, setSelectedSeason] = usePersistedState("telemetry-season", String(currentYear));
const [selectedGP, setSelectedGP] = usePersistedState("telemetry-gp", "");
const [selectedSession, setSelectedSession] = usePersistedState("telemetry-session", "Qualifying");
const [selectedDriver, setSelectedDriver] = usePersistedState("telemetry-driver", "");
const [selectedDriver2, setSelectedDriver2] = usePersistedState("telemetry-driver2", "");
```

- [ ] **Step 3: Use the hook in Dashboard for selectedCircuit**

Open `src/pages/Dashboard.tsx`. Replace:
```typescript
const [selectedCircuit, setSelectedCircuit] = useState("");
```
With:
```typescript
import { usePersistedState } from "@/hooks/usePersistedState";

const [selectedCircuit, setSelectedCircuit] = usePersistedState("dashboard-circuit", "");
```

- [ ] **Step 4: Verify persistence works**

```bash
npm run dev
```
1. Open http://localhost:5173/telemetry
2. Select a season, GP, session, and driver
3. Refresh the page (Cmd+R)
4. The selections should be restored automatically

- [ ] **Step 5: Verify fresh state when selections become invalid**

The hook stores as-is. If a stored GP name no longer exists in the new season's race list, the Select will show nothing selected — that's acceptable behavior (the dropdown defaults to the placeholder). No crash should occur.

- [ ] **Step 6: Commit**

```bash
git add src/hooks/usePersistedState.ts src/pages/TelemetryAnalyzer.tsx src/pages/Dashboard.tsx
git commit -m "feat: persist race/driver/session selections to localStorage across refreshes"
```

---

## Chunk 3: Live championship refresh with "last updated" indicator

### Task 3: Add visible refresh indicator to Dashboard championship section

**Files:**
- Modify: `src/pages/Dashboard.tsx`

The `refetchInterval` is already set on `liveChampionshipApi` in the performance plan. This task adds the visible "last updated X seconds ago" text so users know the data is live.

- [ ] **Step 1: Find the championship standings section in Dashboard.tsx**

```bash
grep -n "championship\|standings\|liveChampionship" src/pages/Dashboard.tsx | head -20
```

Note the line where championship data is rendered in JSX.

- [ ] **Step 2: Add a "last updated" display**

Near the championship panel heading in the JSX, add:

```tsx
import { useQueryClient } from "@tanstack/react-query";

// Inside the component:
const queryClient = useQueryClient();
const championshipState = queryClient.getQueryState(["championship-standings"]);
const lastUpdatedMs = championshipState?.dataUpdatedAt;
const secondsAgo = lastUpdatedMs
  ? Math.floor((Date.now() - lastUpdatedMs) / 1000)
  : null;

// In JSX near the championship panel title:
{secondsAgo !== null && (
  <span className="text-xs text-gray-500">
    Updated {secondsAgo < 60 ? `${secondsAgo}s ago` : `${Math.floor(secondsAgo / 60)}m ago`}
  </span>
)}
```

- [ ] **Step 3: Verify auto-refresh works**

Open http://localhost:5173/dashboard and watch the "Updated X seconds ago" text. It should reset to "0s ago" every 10 minutes as the query auto-refreshes.

To test faster, temporarily set `refetchInterval: 10_000` (10 seconds), watch the counter reset, then restore to `60_000 * 10`.

- [ ] **Step 4: Commit**

```bash
git add src/pages/Dashboard.tsx
git commit -m "feat: show last-updated timestamp on live championship standings"
```
