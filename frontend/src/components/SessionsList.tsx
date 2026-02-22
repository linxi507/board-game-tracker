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
    <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8 }}>
      <h2 style={{ marginTop: 0 }}>Session History</h2>
      {loading && <p>Loading sessions...</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {!loading && !error && sessions.length === 0 && <p>No sessions yet.</p>}
      {!loading && !error && sessions.length > 0 && (
        <ul style={{ paddingLeft: 20, margin: 0 }}>
          {sessions.map((session) => (
            <li key={session.id} style={{ marginBottom: 10 }}>
              <div>Game ID: {session.board_game.id}</div>
              <div>player_count: {session.player_count}</div>
              <div>played_date: {formatPlayedDate(session.played_at)}</div>
              <div>placement: {session.placement ?? "-"}</div>
              <div>duration_minutes: {session.duration_minutes ?? "-"}</div>
              <div>created_at: {session.created_at}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
