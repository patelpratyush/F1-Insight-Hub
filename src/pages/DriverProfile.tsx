import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import DataWrapper from "@/components/ui/data-wrapper";
import { API_BASE } from "@/lib/api";
import { useFavorites } from "@/hooks/useFavorites";
import { useQuery } from "@tanstack/react-query";
import { Star, Trophy } from "lucide-react";
import { useParams } from "react-router-dom";

interface Season {
  year: number;
  position: number;
  points: number;
  wins: number;
  team: string;
  regulation_era: string;
}

interface DriverProfileData {
  code: string;
  name: string;
  current_team: string;
  seasons: Season[];
  career_totals: {
    seasons: number;
    wins: number;
    points: number;
    best_position: number;
  };
}

const DriverProfile = () => {
  const { code } = useParams<{ code: string }>();
  const { isFavorite, toggleFavorite } = useFavorites();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["driver-profile", code],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/f1/driver/${code}?years=6`);
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const json = await response.json();
      return json as DriverProfileData;
    },
    enabled: !!code,
    staleTime: 1000 * 60 * 60,
    retry: 1,
  });

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32">
      <div className="max-w-screen-2xl mx-auto pt-8">
        <AnimatedPageWrapper delay={100}>
          <DataWrapper
            loading={isLoading}
            error={error ? (error as Error).message : null}
            data={data}
            onRetry={refetch}
            isRetrying={isLoading}
            minHeight="min-h-[300px]"
          >
            {data && (
              <div className="flex flex-col gap-12">
                <div className="flex items-start justify-between gap-6">
                  <div className="flex flex-col gap-6">
                    <span className="text-red-500 font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                      DRIVER PROFILE
                    </span>
                    <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
                      {data.name}
                    </h1>
                    <p className="text-white/50 text-xl font-light">
                      {data.current_team} &bull; #{data.code}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleFavorite("driver", data.code)}
                    aria-label={
                      isFavorite("driver", data.code)
                        ? `Remove ${data.name} from favorites`
                        : `Add ${data.name} to favorites`
                    }
                    className="p-4 rounded-full bg-white/5 hover:bg-white/10 transition-colors"
                  >
                    <Star
                      className={`h-6 w-6 ${isFavorite("driver", data.code) ? "fill-yellow-400 text-yellow-400" : "text-white/40"}`}
                    />
                  </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-6 bg-white/5 rounded-[24px] text-center">
                    <Trophy className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
                    <div className="text-2xl font-black text-yellow-400">
                      {data.career_totals.wins}
                    </div>
                    <div className="text-sm text-white/50">
                      Wins ({data.career_totals.seasons}yr window)
                    </div>
                  </div>
                  <div className="p-6 bg-white/5 rounded-[24px] text-center">
                    <div className="text-2xl font-black text-red-400">
                      {data.career_totals.points}
                    </div>
                    <div className="text-sm text-white/50">Total Points</div>
                  </div>
                  <div className="p-6 bg-white/5 rounded-[24px] text-center">
                    <div className="text-2xl font-black text-white">
                      P{data.career_totals.best_position}
                    </div>
                    <div className="text-sm text-white/50">Best Season Finish</div>
                  </div>
                  <div className="p-6 bg-white/5 rounded-[24px] text-center">
                    <div className="text-2xl font-black text-white">
                      {data.career_totals.seasons}
                    </div>
                    <div className="text-sm text-white/50">Seasons Tracked</div>
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <h2 className="text-2xl font-black tracking-tighter mb-2">
                    SEASON BY SEASON
                  </h2>
                  {data.seasons.map((s) => (
                    <div
                      key={s.year}
                      className="flex items-center justify-between p-4 bg-white/5 rounded-[16px]"
                    >
                      <div className="flex items-center gap-4">
                        <span className="font-bold text-lg w-16">
                          {s.year}
                        </span>
                        <span className="text-white/70">{s.team}</span>
                        <span className="text-white/30 text-xs uppercase tracking-widest">
                          {s.regulation_era}
                        </span>
                      </div>
                      <div className="flex items-center gap-6">
                        <span className="text-white/50 text-sm">
                          {s.wins} {s.wins === 1 ? "win" : "wins"}
                        </span>
                        <span className="text-white/70 font-mono">
                          {s.points} pts
                        </span>
                        <span className="font-black text-lg w-10 text-right">
                          P{s.position}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </DataWrapper>
        </AnimatedPageWrapper>
      </div>
    </div>
  );
};

export default DriverProfile;
