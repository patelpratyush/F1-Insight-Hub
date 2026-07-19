import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import LapSelector from "@/components/LapSelector";
import RaceSelect from "@/components/RaceSelect";
import DataWrapper from "@/components/ui/data-wrapper";
import { API_BASE } from "@/lib/api";
import { getCurrentSeasonYear } from "@/lib/season";
import { useTracks } from "@/hooks/useF1Metadata";
import { useQuery } from "@tanstack/react-query";
import { Flag } from "lucide-react";
import { useEffect, useState } from "react";

interface LapTiming {
  driver: string;
  position: number;
  time: string;
}

interface Lap {
  lap: number;
  timings: LapTiming[];
}

const LapReplay = () => {
  const currentSeasonYear = getCurrentSeasonYear();
  const [selectedTrack, setSelectedTrack] = useState("");
  const [selectedLap, setSelectedLap] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  const { data: apiTracks } = useTracks(currentSeasonYear);
  const round = apiTracks?.find((t) => t.race_name === selectedTrack)?.round;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["lap-replay", currentSeasonYear, round],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/api/results/laps/${currentSeasonYear}/${round}`,
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const json = await response.json();
      return json.laps as Lap[];
    },
    enabled: !!round,
    staleTime: 1000 * 60 * 60,
    retry: 2,
  });

  const laps = data || [];
  const availableLaps = laps.map((l) => l.lap);

  useEffect(() => {
    setSelectedLap(availableLaps[0] || 1);
    setIsPlaying(false);
  }, [round]);

  const currentLap = laps.find((l) => l.lap === selectedLap);
  const positions = [...(currentLap?.timings || [])].sort(
    (a, b) => a.position - b.position,
  );

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32">
      <div className="max-w-screen-2xl mx-auto pt-8">
        <AnimatedPageWrapper delay={100}>
          <div className="flex flex-col mb-16 gap-6">
            <span className="text-red-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              LAP-BY-LAP DATA
            </span>
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
              LAP
              <br />
              REPLAY
            </h1>
            <p className="text-white/50 text-xl font-light max-w-2xl mt-4">
              Step through official lap timing to see the running order
              change lap by lap.
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
              data={laps}
              onRetry={refetch}
              isRetrying={isLoading}
              minHeight="min-h-[300px]"
            >
              {laps.length === 0 ? (
                <p className="text-white/40">No lap data for this race.</p>
              ) : (
                <div className="flex flex-col gap-8">
                  <LapSelector
                    availableLaps={availableLaps}
                    selectedLap={selectedLap}
                    onLapChange={setSelectedLap}
                    isPlaying={isPlaying}
                    onPlayStateChange={setIsPlaying}
                    playbackSpeed={playbackSpeed}
                    onSpeedChange={setPlaybackSpeed}
                  />

                  <div className="flex flex-col gap-2">
                    {positions.map((p) => (
                      <div
                        key={p.driver}
                        className="flex items-center justify-between p-4 bg-white/5 rounded-[16px]"
                      >
                        <div className="flex items-center gap-4">
                          <span
                            className={`text-xl font-black w-8 ${p.position <= 3 ? "text-yellow-400" : "text-white/60"}`}
                          >
                            {p.position}
                          </span>
                          <span className="font-bold text-lg">
                            {p.driver}
                          </span>
                          {p.position === 1 && (
                            <Flag className="h-4 w-4 text-yellow-400" />
                          )}
                        </div>
                        <span className="font-mono text-white/70">
                          {p.time}
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

export default LapReplay;
