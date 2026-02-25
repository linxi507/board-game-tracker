import { apiFetch } from "./client";

export type FavoriteGame = {
  id: number;
  board_game: {
    id: number;
    name: string;
  };
  created_at: string;
};

export type FavoriteToggleResult = {
  board_game_id: number;
  is_favorite: boolean;
};

export type CustomGame = {
  id: number;
  name: string;
  created_at: string;
};

export async function fetchFavorites(): Promise<FavoriteGame[]> {
  return (await apiFetch("/me/favorites")) as FavoriteGame[];
}

export async function toggleFavorite(boardGameId: number): Promise<FavoriteToggleResult> {
  return (await apiFetch(`/me/favorites/${boardGameId}`, {
    method: "POST",
  })) as FavoriteToggleResult;
}

export async function fetchCustomGames(): Promise<CustomGame[]> {
  return (await apiFetch("/me/custom-games")) as CustomGame[];
}

export async function createCustomGame(name: string): Promise<CustomGame> {
  return (await apiFetch("/me/custom-games", {
    method: "POST",
    body: JSON.stringify({ name }),
  })) as CustomGame;
}
