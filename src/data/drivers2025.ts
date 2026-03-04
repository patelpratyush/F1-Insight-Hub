/**
 * F1 Driver Types - re-exports from the dynamic hook.
 * Legacy file kept for backward compatibility.
 * Prefer using useDrivers() from @/hooks/useF1Metadata instead.
 */

export type { Driver } from "@/hooks/useF1Metadata";
export { useDrivers, useDriverCodes } from "@/hooks/useF1Metadata";
