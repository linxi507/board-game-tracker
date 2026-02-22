import { useEffect, useState } from "react";

import { fetchStatsSummary, StatsSummary } from "../api/stats";

type Props = {
  reloadSignal: number;
};

export default function StatsPanel({ reloadSignal }: Props) {
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      setError("");
      try {
        const summary = await fetchStatsSummary();
        setStats(summary);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load stats");
      } finally {
        setLoading(false);
      }
    }

    void loadStats();
  }, [reloadSignal]);

  return (
    <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h2 style={{ marginTop: 0 }}>Stats Summary</h2>
      {loading && <p>Loading stats...</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {!loading && !error && stats && (
        <>
          <div style={{ display: "grid", gap: 6 }}>
            <div>Total sessions: {stats.total_sessions}</div>
            <div>Total play time (minutes): {stats.total_play_time_minutes}</div>
            <div>
              Avg duration:{" "}
              {stats.average_duration_minutes === null
                ? "-"
                : stats.average_duration_minutes.toFixed(2)}
            </div>
            <div>
              Win rate:{" "}
              {stats.win_rate === null ? "-" : `${(stats.win_rate * 100).toFixed(2)}%`}
            </div>
            <div>Sessions last 30 days: {stats.sessions_last_30_days}</div>
          </div>

          <h3 style={{ marginBottom: 8 }}>Top Played Games</h3>
          {stats.most_played_games.length === 0 && <p style={{ marginTop: 0 }}>No games played yet.</p>}
          {stats.most_played_games.length > 0 && (
            <ul style={{ marginTop: 0, paddingLeft: 20 }}>
              {stats.most_played_games.map((game) => (
                <li key={game.board_game_id}>
                  {game.name} ({game.session_count})
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
