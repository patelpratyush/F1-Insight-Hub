import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import { useFavorites } from "@/hooks/useFavorites";
import { getCurrentSeasonYear } from "@/lib/season";
import { useDrivers } from "@/hooks/useF1Metadata";
import { Star, X } from "lucide-react";
import { Link } from "react-router-dom";

const Favorites = () => {
  const currentYear = getCurrentSeasonYear();
  const { favorites, toggleFavorite } = useFavorites();
  const { data: drivers } = useDrivers(currentYear);

  const driverName = (code: string) =>
    drivers?.find((d) => d.code === code.toUpperCase())?.name || code.toUpperCase();

  const profileHref = (kind: string, id: string) =>
    kind === "driver" ? `/drivers/${id.toUpperCase()}` : `/teams/${encodeURIComponent(id)}`;

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32">
      <div className="max-w-screen-2xl mx-auto pt-8">
        <AnimatedPageWrapper delay={100}>
          <div className="flex flex-col mb-16 gap-6">
            <span className="text-red-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              SAVED LOCALLY
            </span>
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
              FAVORITES
            </h1>
            <p className="text-white/50 text-xl font-light max-w-2xl mt-4">
              Saved to this browser only — no account required.
            </p>
          </div>
        </AnimatedPageWrapper>

        <AnimatedPageWrapper delay={400}>
          {favorites.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <Star className="h-16 w-16 text-white/10 mb-6" />
              <h3 className="text-2xl font-black text-white/80 mb-2">
                NO FAVORITES YET
              </h3>
              <p className="text-white/40 max-w-sm">
                Star a driver or team from their profile page to see it here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {favorites.map((fav) => (
                <div
                  key={`${fav.kind}:${fav.id}`}
                  className="flex items-center justify-between p-6 bg-white/5 rounded-[24px]"
                >
                  <Link
                    to={profileHref(fav.kind, fav.id)}
                    className="flex flex-col hover:text-red-500 transition-colors"
                  >
                    <span className="font-bold text-lg">
                      {fav.kind === "driver" ? driverName(fav.id) : fav.id}
                    </span>
                    <span className="text-white/40 text-xs uppercase tracking-widest">
                      {fav.kind}
                    </span>
                  </Link>
                  <button
                    type="button"
                    onClick={() => toggleFavorite(fav.kind, fav.id)}
                    aria-label={`Remove ${fav.id} from favorites`}
                    className="p-2 rounded-full hover:bg-white/10 transition-colors"
                  >
                    <X className="h-4 w-4 text-white/40" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </AnimatedPageWrapper>
      </div>
    </div>
  );
};

export default Favorites;
