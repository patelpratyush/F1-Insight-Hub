import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import DataWrapper from "@/components/ui/data-wrapper";
import { API_BASE } from "@/lib/api";
import { getCurrentSeasonYear } from "@/lib/season";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useState } from "react";

interface StandingEntry {
  position: number;
  driver?: string;
  name?: string;
  team_name?: string;
  points: number;
  wins: number;
}

interface SeasonData {
  year: number;
  regulation_era: string;
  driver_standings: StandingEntry[];
  constructor_standings: StandingEntry[];
}

const SeasonComparison = () => {
  const currentYear = getCurrentSeasonYear();
  const [years, setYears] = useState<number[]>([currentYear, currentYear - 1]);
  const yearOptions = Array.from({ length: 8 }, (_, i) => currentYear - i);

  const yearsParam = [...years].sort().join(",");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["compare-seasons", yearsParam],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/api/f1/compare-seasons?years=${yearsParam}`,
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const json = await response.json();
      return json as { years: number[]; seasons: SeasonData[]; spans_regulation_change: boolean };
    },
    enabled: years.length >= 2,
    staleTime: 1000 * 60 * 60,
    retry: 1,
  });

  const toggleYear = (year: number) => {
    setYears((prev) =>
      prev.includes(year)
        ? prev.filter((y) => y !== year)
        : [...prev, year],
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32">
      <div className="max-w-screen-2xl mx-auto pt-8">
        <AnimatedPageWrapper delay={100}>
          <div className="flex flex-col mb-16 gap-6">
            <span className="text-red-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              CROSS-SEASON DATA
            </span>
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
              SEASON
              <br />
              COMPARISON
            </h1>
          </div>
        </AnimatedPageWrapper>

        <AnimatedPageWrapper delay={400}>
          <div className="flex flex-wrap gap-2 mb-8">
            {yearOptions.map((year) => (
              <button
                key={year}
                type="button"
                onClick={() => toggleYear(year)}
                className={`px-5 py-2.5 rounded-full text-sm font-bold transition-all ${
                  years.includes(year)
                    ? "bg-white text-black"
                    : "bg-white/5 text-white/50 hover:text-white"
                }`}
              >
                {year}
              </button>
            ))}
          </div>
        </AnimatedPageWrapper>

        {years.length < 2 ? (
          <p className="text-white/40">Select at least 2 seasons to compare.</p>
        ) : (
          <AnimatedPageWrapper delay={600}>
            <DataWrapper
              loading={isLoading}
              error={error ? (error as Error).message : null}
              data={data}
              onRetry={refetch}
              isRetrying={isLoading}
              minHeight="min-h-[300px]"
            >
              {data && (
                <div className="flex flex-col gap-8">
                  {data.spans_regulation_change && (
                    <div className="flex items-center gap-3 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-[16px] text-yellow-400 text-sm">
                      <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                      <span>
                        These seasons span a regulation change — car
                        performance and points totals aren't directly
                        comparable across eras.
                      </span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {data.seasons.map((season) => (
                      <div key={season.year} className="p-6 bg-white/5 rounded-[24px]">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-2xl font-black">{season.year}</h3>
                          <span className="text-xs text-white/40 uppercase tracking-widest">
                            {season.regulation_era}
                          </span>
                        </div>
                        <h4 className="text-white/50 text-xs font-bold uppercase tracking-widest mb-2">
                          Top 5 Drivers
                        </h4>
                        <div className="flex flex-col gap-1 mb-4">
                          {season.driver_standings.slice(0, 5).map((d) => (
                            <div
                              key={d.driver}
                              className="flex items-center justify-between text-sm py-1"
                            >
                              <span>
                                P{d.position} {d.name}
                              </span>
                              <span className="font-mono text-white/60">
                                {d.points} pts
                              </span>
                            </div>
                          ))}
                        </div>
                        <h4 className="text-white/50 text-xs font-bold uppercase tracking-widest mb-2">
                          Top 3 Teams
                        </h4>
                        <div className="flex flex-col gap-1">
                          {season.constructor_standings.slice(0, 3).map((t) => (
                            <div
                              key={t.team_name}
                              className="flex items-center justify-between text-sm py-1"
                            >
                              <span>
                                P{t.position} {t.team_name}
                              </span>
                              <span className="font-mono text-white/60">
                                {t.points} pts
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </DataWrapper>
          </AnimatedPageWrapper>
        )}
      </div>
    </div>
  );
};

export default SeasonComparison;
