import { useQuery } from "@tanstack/react-query";
import { getCurrentSeasonYear } from "@/lib/season";
import { API_BASE } from "@/lib/api";
const CURRENT_YEAR = getCurrentSeasonYear();

export interface Driver {
  id: string;
  code: string;
  name: string;
  team: string;
  number: string;
  nationality: string;
  teamColor: string;
}

export interface Track {
  round: number;
  race_name: string;
  date: string;
  circuit: string;
  location: string;
  country: string;
}

const TEAM_COLORS: Record<string, string> = {
  McLaren: "#FF8700",
  Ferrari: "#DC143C",
  "Scuderia Ferrari": "#DC143C",
  Mercedes: "#00D2BE",
  "Red Bull": "#0600EF",
  "Red Bull Racing": "#0600EF",
  "Aston Martin": "#006F62",
  Alpine: "#0090FF",
  "Alpine F1 Team": "#0090FF",
  Williams: "#005AFF",
  "Racing Bulls": "#6692FF",
  "RB F1 Team": "#6692FF",
  Haas: "#B6BABD",
  "Haas F1 Team": "#B6BABD",
  "MoneyGram Haas F1 Team": "#B6BABD",
  "Kick Sauber": "#52E252",
  Sauber: "#52E252",
  "Stake F1 Team Kick Sauber": "#52E252",
};

function resolveTeamColor(team: string): string {
  if (TEAM_COLORS[team]) return TEAM_COLORS[team];
  for (const [key, color] of Object.entries(TEAM_COLORS)) {
    if (team.includes(key) || key.includes(team)) return color;
  }
  return "#888888";
}

async function fetchDrivers(year: number): Promise<Driver[]> {
  const resp = await fetch(`${API_BASE}/api/metadata/drivers/${year}`);
  if (!resp.ok) throw new Error(`Failed to fetch drivers: ${resp.status}`);
  const data = await resp.json();
  if (!data.success) throw new Error("API returned failure");

  return (data.drivers || [])
    .filter((d: any) => d.code)
    .map((d: any) => ({
      id: d.code,
      code: d.code,
      name: d.name || "",
      team: d.team || "",
      number: d.number || "",
      nationality: d.nationality || "",
      teamColor: resolveTeamColor(d.team || ""),
    }));
}

async function fetchTracks(year: number): Promise<Track[]> {
  const resp = await fetch(`${API_BASE}/api/metadata/tracks/${year}`);
  if (!resp.ok) throw new Error(`Failed to fetch tracks: ${resp.status}`);
  const data = await resp.json();
  if (!data.success) throw new Error("API returned failure");
  return data.tracks || [];
}

export function useDrivers(year: number = CURRENT_YEAR) {
  return useQuery<Driver[]>({
    queryKey: ["f1-drivers", year],
    queryFn: () => fetchDrivers(year),
    staleTime: 1000 * 60 * 60,
    retry: 2,
  });
}

export function useTracks(year: number = CURRENT_YEAR) {
  return useQuery<Track[]>({
    queryKey: ["f1-tracks", year],
    queryFn: () => fetchTracks(year),
    staleTime: 1000 * 60 * 60,
    retry: 2,
  });
}

export function useTrackNames(year: number = CURRENT_YEAR) {
  const { data: tracks, ...rest } = useTracks(year);
  return {
    ...rest,
    data: tracks?.map((t) => t.race_name) || [],
  };
}

export function useDriverCodes(year: number = CURRENT_YEAR) {
  const { data: drivers, ...rest } = useDrivers(year);
  return {
    ...rest,
    data: drivers?.map((d) => d.code) || [],
  };
}
