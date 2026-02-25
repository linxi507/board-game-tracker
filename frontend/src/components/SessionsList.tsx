import { useEffect, useState } from "react";

import { fetchSessions, SessionItem } from "../api/sessions";

type Props = {
  reloadSignal: number;
};

export default function SessionsList({ reloadSignal }: Props) {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSessions() {
      setLoading(true);
      setError("");
      try {
        const items = await fetchSessions();
        setSessions(items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load sessions");
      } finally {
        setLoading(false);
      }
    }

    void loadSessions();
  }, [reloadSignal]);

  function formatPlayedDate(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    const month = String(date.getUTCMonth() + 1).padStart(2, "0");
    const day = String(date.getUTCDate()).padStart(2, "0");
    const year = date.getUTCFullYear();
    return `${month}/${day}/${year}`;
  }

  return (
    <section className="panel">
      <h2 className="panel-title">Recent Sessions</h2>
      {loading && <p>Loading sessions...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && sessions.length === 0 && <p className="meta-text">No sessions yet.</p>}
      {!loading && !error && sessions.length > 0 && (
        <ul className="session-list">
          {sessions.map((session) => (
            <li key={session.id} className="session-item">
              <div>
                <strong>
                  {session.board_game?.name ?? session.user_custom_game?.name ?? "Unknown game"}
                </strong>{" "}
                {session.board_game ? `(#${session.board_game.id})` : "(custom)"}
              </div>
              <div>Players: {session.player_count}</div>
              <div>Played: {formatPlayedDate(session.played_at)}</div>
              <div>Placement: {session.placement ?? "-"}</div>
              <div>Duration: {session.duration_minutes ?? "-"} min</div>
              <div className="meta-text">Created: {session.created_at}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
