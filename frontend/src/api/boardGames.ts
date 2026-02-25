import { apiFetch } from "./client";

export type BoardGame = {
  id: number;
  name: string;
  source: string | null;
  source_id: string | null;
  created_at: string;
};

export type BoardGameSearchItem = {
  key: string;
  id: number;
  name: string;
  source: "global" | "custom";
  is_favorite: boolean;
};

export async function fetchBoardGames(query?: string): Promise<BoardGame[]> {
  const search = query?.trim();
  const path = search
    ? `/board-games?query=${encodeURIComponent(search)}`
    : "/board-games";
  return (await apiFetch(path)) as BoardGame[];
}

export async function searchBoardGames(
  query: string,
  limit = 20
): Promise<BoardGameSearchItem[]> {
  const params = new URLSearchParams();
  params.set("query", query);
  params.set("limit", String(limit));
  return (await apiFetch(`/board-games/search?${params.toString()}`)) as BoardGameSearchItem[];
}
