# F1 Insight Hub - Data Layer

## 📊 Centralized Driver Data

This directory contains centralized data structures used across all components to ensure consistency.

### `drivers2025.ts`

Contains the complete 2025 F1 driver grid with standardized format:

```typescript
interface Driver {
  id: string;      // Driver code (e.g., "VER", "HAM")
  name: string;    // Full name (e.g., "Max Verstappen")
  team: string;    // Team name (e.g., "Red Bull Racing")
  number: number;  // Racing number (e.g., 1, 44)
  teamColor?: string; // Optional team color for UI
}
```

### Usage

**Import the complete driver array:**
```typescript
import { drivers2025 } from "@/data/drivers2025";
```

**Import just driver codes (for telemetry):**
```typescript
import { driverCodes } from "@/data/drivers2025";
```

**Import helper functions:**
```typescript
import { getDriverById, getDriversByTeam, getTeamNames } from "@/data/drivers2025";
```

### Components Using This Data

- ✅ **DriverSelect.tsx** - Standard driver selection component
- ✅ **DriverPredictor.tsx** - Individual driver performance predictions
- ✅ **StrategySimulator.tsx** - Race strategy simulation
- ✅ **TelemetryAnalyzer.tsx** - Telemetry analysis (uses driverCodes)
- ✅ **PredictionForm.tsx** - Uses DriverSelect component

### 2025 F1 Grid Changes

**Major Transfers:**
- Lewis Hamilton → Ferrari (#44)
- Carlos Sainz → Williams (#55)
- Kimi Antonelli → Mercedes (#12) - Rookie
- Liam Lawson → RB (#30)

**New Rookies:**
- Oliver Bearman → Haas (#38)
- Gabriel Bortoleto → Kick Sauber (#5)
- Isack Hadjar → Kick Sauber (#6)

All components now use this centralized data source to ensure consistency across the application.