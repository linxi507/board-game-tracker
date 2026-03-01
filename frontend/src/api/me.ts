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

export async function addFavorite(boardGameId: number): Promise<FavoriteToggleResult> {
  return (await apiFetch("/me/favorites", {
    method: "POST",
    body: JSON.stringify({ board_game_id: boardGameId }),
  })) as FavoriteToggleResult;
}

export async function removeFavorite(boardGameId: number): Promise<FavoriteToggleResult> {
  return (await apiFetch(`/me/favorites/${boardGameId}`, {
    method: "DELETE",
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

export async function deleteCustomGame(customGameId: number): Promise<void> {
  await apiFetch(`/me/custom-games/${customGameId}`, {
    method: "DELETE",
  });
}
