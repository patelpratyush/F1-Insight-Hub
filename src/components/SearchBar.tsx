import { useDrivers, useTracks } from "@/hooks/useF1Metadata";
import { getCurrentSeasonYear } from "@/lib/season";
import { Search, X } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

interface SearchResult {
  label: string;
  sublabel: string;
  href: string;
}

const SearchBar = () => {
  const currentYear = getCurrentSeasonYear();
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: drivers } = useDrivers(currentYear);
  const { data: tracks } = useTracks(currentYear);

  const results = useMemo<SearchResult[]>(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];

    const driverResults: SearchResult[] = (drivers || [])
      .filter(
        (d) =>
          d.name.toLowerCase().includes(q) || d.code.toLowerCase().includes(q),
      )
      .map((d) => ({
        label: d.name,
        sublabel: `Driver • ${d.team}`,
        href: `/drivers/${d.code}`,
      }));

    const teamNames = Array.from(
      new Set((drivers || []).map((d) => d.team)),
    );
    const teamResults: SearchResult[] = teamNames
      .filter((t) => t.toLowerCase().includes(q))
      .map((t) => ({
        label: t,
        sublabel: "Team",
        href: `/teams/${encodeURIComponent(t)}`,
      }));

    const trackResults: SearchResult[] = (tracks || [])
      .filter((t) => t.race_name.toLowerCase().includes(q))
      .map((t) => ({
        label: t.race_name,
        sublabel: `Round ${t.round} • ${t.location}`,
        href: `/pit-stops`,
      }));

    return [...driverResults, ...teamResults, ...trackResults].slice(0, 8);
  }, [query, drivers, tracks]);

  const handleSelect = (href: string) => {
    setQuery("");
    setIsOpen(false);
    navigate(href);
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-white/5 rounded-full px-4 py-2 border border-white/10 focus-within:border-white/30 transition-colors">
        <Search className="h-4 w-4 text-white/40 flex-shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 150)}
          placeholder="Search drivers, teams, races..."
          aria-label="Search drivers, teams, and races"
          className="bg-transparent text-sm text-white placeholder:text-white/30 outline-none w-40 md:w-56"
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            aria-label="Clear search"
            className="text-white/40 hover:text-white"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-[#111111] border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-50">
          {results.map((r) => (
            <button
              key={`${r.href}-${r.label}`}
              type="button"
              onClick={() => handleSelect(r.href)}
              className="w-full text-left px-4 py-3 hover:bg-white/10 transition-colors flex flex-col"
            >
              <span className="text-white text-sm font-medium">{r.label}</span>
              <span className="text-white/40 text-xs">{r.sublabel}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
