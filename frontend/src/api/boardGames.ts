import { getToken } from "./client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type BoardGame = {
  key: string;
  id: number;
  name: string;
  source: "global" | "custom";
  is_favorite: boolean;
};

export type BoardGamesPage = {
  items: BoardGame[];
  total: number;
  limit: number;
  offset: number;
};

export async function fetchBoardGames(
  q = "",
  limit = 20,
  offset = 0
): Promise<BoardGamesPage> {
  const token = getToken();
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const params = new URLSearchParams();
  if (q.trim()) {
    params.set("q", q.trim());
  }
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const response = await fetch(`${API_BASE_URL}/board-games?${params.toString()}`, {
    headers,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = `${String(body.detail)} (${response.status})`;
      }
    } catch {
      // Use default error.
    }
    throw new Error(detail);
  }

  const items = (await response.json()) as BoardGame[];
  return {
    items,
    total: Number(response.headers.get("X-Total-Count") ?? items.length),
    limit: Number(response.headers.get("X-Limit") ?? limit),
    offset: Number(response.headers.get("X-Offset") ?? offset),
  };
}
