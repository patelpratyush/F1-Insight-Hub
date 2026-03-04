/**
 * F1 Track Types - re-exports from the dynamic hook.
 * Legacy file kept for backward compatibility.
 * Prefer using useTracks() from @/hooks/useF1Metadata instead.
 */

export type { Track as F1Track } from "@/hooks/useF1Metadata";
export { useTracks, useTrackNames } from "@/hooks/useF1Metadata";
