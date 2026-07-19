import { usePersistedState } from "@/hooks/usePersistedState";

export type FavoriteKind = "driver" | "team" | "track";

export interface FavoriteEntry {
  kind: FavoriteKind;
  id: string;
}

function favoriteKey(kind: FavoriteKind, id: string): string {
  return `${kind}:${id.toLowerCase()}`;
}

export function useFavorites() {
  const [favorites, setFavorites] = usePersistedState<FavoriteEntry[]>(
    "f1-favorites",
    [],
  );

  const isFavorite = (kind: FavoriteKind, id: string) =>
    favorites.some((f) => favoriteKey(f.kind, f.id) === favoriteKey(kind, id));

  const toggleFavorite = (kind: FavoriteKind, id: string) => {
    setFavorites((prev) =>
      isFavorite(kind, id)
        ? prev.filter((f) => favoriteKey(f.kind, f.id) !== favoriteKey(kind, id))
        : [...prev, { kind, id }],
    );
  };

  return { favorites, isFavorite, toggleFavorite };
}
