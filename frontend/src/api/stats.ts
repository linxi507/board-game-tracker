import { apiFetch } from "./client";

export type MostPlayedGame = {
  board_game_id: number;
  name: string;
  session_count: number;
};

export type StatsSummary = {
  total_sessions: number;
  total_play_time_minutes: number;
  average_duration_minutes: number | null;
  win_count: number;
  win_rate: number | null;
  sessions_last_30_days: number;
  most_played_games: MostPlayedGame[];
};

export async function fetchStatsSummary(): Promise<StatsSummary> {
  return (await apiFetch("/stats/summary")) as StatsSummary;
}
