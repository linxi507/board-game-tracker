import { apiFetch } from "./client";

export type BoardGame = {
  id: number;
  name: string;
  source: string | null;
  source_id: string | null;
  created_at: string;
};

export async function fetchBoardGames(query?: string): Promise<BoardGame[]> {
  const search = query?.trim();
  const path = search ? `/board-games?q=${encodeURIComponent(search)}` : "/board-games";
  return (await apiFetch(path)) as BoardGame[];
}
