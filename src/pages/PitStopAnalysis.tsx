import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import RaceSelect from "@/components/RaceSelect";
import DataWrapper from "@/components/ui/data-wrapper";
import { API_BASE } from "@/lib/api";
import { getCurrentSeasonYear } from "@/lib/season";
import { useTracks } from "@/hooks/useF1Metadata";
import { useQuery } from "@tanstack/react-query";
import { Timer } from "lucide-react";
import { useState } from "react";

const PitStopAnalysis = () => {
  const currentSeasonYear = getCurrentSeasonYear();
  const [selectedTrack, setSelectedTrack] = useState("");

  const { data: apiTracks } = useTracks(currentSeasonYear);
  const round = apiTracks?.find((t) => t.race_name === selectedTrack)?.round;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["pit-stops", currentSeasonYear, round],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/api/results/pit-stops/${currentSeasonYear}/${round}`,
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const json = await response.json();
      return json.pit_stops as {
        driver: string;
        lap: number;
        stop_number: number;
        duration_s: number | null;
      }[];
    },
    enabled: !!round,
    staleTime: 1000 * 60 * 60,
    retry: 2,
  });

  const stops = data || [];
  const sortedByDuration = [...stops]
    .filter((s) => s.duration_s != null)
    .sort((a, b) => (a.duration_s as number) - (b.duration_s as number));
  const fastest = sortedByDuration[0];
  const avgDuration = sortedByDuration.length
    ? sortedByDuration.reduce((sum, s) => sum + (s.duration_s as number), 0) / sortedByDuration.length
    : null;

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32">
      <div className="max-w-screen-2xl mx-auto pt-8">
        <AnimatedPageWrapper delay={100}>
          <div className="flex flex-col mb-16 gap-6">
            <span className="text-red-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              PIT LANE DATA
            </span>
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
              PIT STOP
              <br />
              ANALYSIS
            </h1>
            <p className="text-white/50 text-xl font-light max-w-2xl mt-4">
              Real pit stop timing for every driver in a race, sourced from
              official timing data.
            </p>
          </div>
        </AnimatedPageWrapper>

        <AnimatedPageWrapper delay={400}>
          <div className="mb-8 max-w-md">
            <RaceSelect
              value={selectedTrack}
              onValueChange={setSelectedTrack}
              tracks={apiTracks}
              placeholder="Select a race"
            />
          </div>
        </AnimatedPageWrapper>

        {selectedTrack && (
          <AnimatedPageWrapper delay={600}>
            <DataWrapper
              loading={isLoading}
              error={error ? (error as Error).message : null}
              data={stops}
              onRetry={refetch}
              isRetrying={isLoading}
              minHeight="min-h-[300px]"
            >
              {stops.length === 0 ? (
                <p className="text-white/40">No pit stop data for this race.</p>
              ) : (
                <div className="flex flex-col gap-8">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-6 bg-white/5 rounded-[24px] text-center">
                      <Timer className="h-6 w-6 text-red-400 mx-auto mb-2" />
                      <div className="text-2xl font-black text-red-400">
                        {stops.length}
                      </div>
                      <div className="text-sm text-white/50">Total Stops</div>
                    </div>
                    <div className="p-6 bg-white/5 rounded-[24px] text-center">
                      <div className="text-2xl font-black text-green-400">
                        {fastest ? `${fastest.duration_s?.toFixed(2)}s` : "N/A"}
                      </div>
                      <div className="text-sm text-white/50">
                        Fastest Stop {fastest ? `(${fastest.driver})` : ""}
                      </div>
                    </div>
                    <div className="p-6 bg-white/5 rounded-[24px] text-center">
                      <div className="text-2xl font-black text-blue-400">
                        {avgDuration ? `${avgDuration.toFixed(2)}s` : "N/A"}
                      </div>
                      <div className="text-sm text-white/50">Average Stop</div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    {[...stops]
                      .sort((a, b) => a.lap - b.lap)
                      .map((stop, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-4 bg-white/5 rounded-[16px]"
                        >
                          <div className="flex items-center gap-4">
                            <span className="font-bold text-lg w-16">
                              {stop.driver}
                            </span>
                            <span className="text-white/50 text-sm">
                              Lap {stop.lap} &bull; Stop #{stop.stop_number}
                            </span>
                          </div>
                          <span
                            className={`font-mono font-bold ${
                              fastest && stop.duration_s === fastest.duration_s
                                ? "text-green-400"
                                : "text-white"
                            }`}
                          >
                            {stop.duration_s != null
                              ? `${stop.duration_s.toFixed(2)}s`
                              : "N/A"}
                          </span>
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

export default PitStopAnalysis;
