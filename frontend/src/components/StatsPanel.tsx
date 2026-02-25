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
    <section className="panel">
      <h2 className="panel-title">Session Pulse</h2>
      {loading && <p>Loading stats...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && stats && (
        <>
          <div className="stats-grid">
            <div className="stats-item">
              <p className="stats-label">Total sessions</p>
              <p className="stats-value">{stats.total_sessions}</p>
            </div>
            <div className="stats-item">
              <p className="stats-label">Play time (minutes)</p>
              <p className="stats-value">{stats.total_play_time_minutes}</p>
            </div>
            <div className="stats-item">
              <p className="stats-label">Avg duration</p>
              <p className="stats-value">
              {stats.average_duration_minutes === null
                ? "-"
                : stats.average_duration_minutes.toFixed(2)}
              </p>
            </div>
            <div className="stats-item">
              <p className="stats-label">Win rate</p>
              <p className="stats-value">
              {stats.win_rate === null ? "-" : `${(stats.win_rate * 100).toFixed(2)}%`}
              </p>
            </div>
            <div className="stats-item">
              <p className="stats-label">Sessions last 30 days</p>
              <p className="stats-value">{stats.sessions_last_30_days}</p>
            </div>
          </div>

          <h3 style={{ margin: "14px 0 8px" }}>Top Played Games</h3>
          {stats.most_played_games.length === 0 && <p className="meta-text">No games played yet.</p>}
          {stats.most_played_games.length > 0 && (
            <ul style={{ marginTop: 0, paddingLeft: 20, display: "grid", gap: 4 }}>
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
