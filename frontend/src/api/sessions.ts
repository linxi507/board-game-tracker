import { apiFetch } from "./client";

export type SessionItem = {
  id: number;
  board_game: {
    id: number;
    name: string;
  } | null;
  user_custom_game: {
    id: number;
    name: string;
  } | null;
  played_at: string;
  player_count: number;
  placement: number | null;
  duration_minutes: number | null;
  notes: string | null;
  created_at: string;
};

export type CreateSessionPayload = {
  board_game_id?: number;
  user_custom_game_id?: number;
  played_date: string;
  player_count: number;
  placement?: number;
  duration_minutes?: number;
  notes?: string;
};

export async function fetchSessions(): Promise<SessionItem[]> {
  return (await apiFetch("/sessions")) as SessionItem[];
}

export async function createSession(payload: CreateSessionPayload): Promise<SessionItem> {
  return (await apiFetch("/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  })) as SessionItem;
}
