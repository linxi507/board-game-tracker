import { FormEvent, useEffect, useState } from "react";

import { BoardGame, fetchBoardGames } from "../api/boardGames";
import { createSession } from "../api/sessions";

type Props = {
  onCreated: () => void;
};

export default function LogSessionForm({ onCreated }: Props) {
  const [query, setQuery] = useState("");
  const [boardGames, setBoardGames] = useState<BoardGame[]>([]);
  const [filteredGames, setFilteredGames] = useState<BoardGame[]>([]);
const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [playedDate, setPlayedDate] = useState("");
  const [playerCount, setPlayerCount] = useState(4);
  const [placement, setPlacement] = useState("");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [notes, setNotes] = useState("");
  const [loadingGames, setLoadingGames] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadBoardGames() {
      try {
        const items = await fetchBoardGames();
        setBoardGames(items);
        setFilteredGames(items);
        if (items.length > 0) {
          setSelectedGameId(items[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load board games");
      } finally {
        setLoadingGames(false);
      }
    }

    void loadBoardGames();
  }, []);

  useEffect(() => {
    const lowerQuery = query.trim().toLowerCase();
    if (!lowerQuery) {
      setFilteredGames(boardGames);
      return;
    }

    const filtered = boardGames.filter((game) =>
      game.name.toLowerCase().includes(lowerQuery)
    );
    setFilteredGames(filtered);
  }, [query, boardGames]);

  const selectedGame = boardGames.find((game) => game.id === selectedGameId) ?? null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!selectedGameId) {
      setError("Please select a board game");
      return;
    }

    setSubmitting(true);
    try {
      if (!/^\d{2}\/\d{2}\/\d{4}$/.test(playedDate)) {
        throw new Error("played_date must be MM/DD/YYYY");
      }
      await createSession({
        board_game_id: selectedGameId,
        played_date: playedDate,
        player_count: Number(playerCount),
        placement: placement ? Number(placement) : undefined,
        duration_minutes: durationMinutes ? Number(durationMinutes) : undefined,
        notes: notes || undefined,
      });

      setPlayerCount(4);
      setPlayedDate("");
      setPlacement("");
      setDurationMinutes("");
      setNotes("");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h2 style={{ marginTop: 0 }}>Log Session</h2>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 10 }}>
        <label>
          Search Board Game
          <input
            type="text"
            placeholder="Search board game..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loadingGames || boardGames.length === 0}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
          />
        </label>

        <div>
          <strong>Selected game:</strong> {selectedGame ? selectedGame.name : "None"}
        </div>

        <div style={{ border: "1px solid #ddd", borderRadius: 6, maxHeight: 180, overflowY: "auto" }}>
          {filteredGames.length === 0 && (
            <div style={{ padding: 8, color: "#555" }}>No matching board games.</div>
          )}
          {filteredGames.map((game) => (
            <button
              key={game.id}
              type="button"
              onClick={() => setSelectedGameId(game.id)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: 8,
                border: "none",
                borderBottom: "1px solid #eee",
                background: selectedGameId === game.id ? "#f0f6ff" : "white",
                cursor: "pointer",
              }}
            >
              {game.name}
            </button>
          ))}
        </div>

        <label>
          Played Date
          <input
            type="text"
            placeholder="MM/DD/YYYY"
            value={playedDate}
            onChange={(e) => setPlayedDate(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
            required
          />
        </label>

        <label>
          Player Count
          <input
            type="number"
            min={1}
            value={playerCount}
            onChange={(e) => setPlayerCount(Number(e.target.value))}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
            required
          />
        </label>

        <label>
          Placement (optional)
          <input
            type="number"
            min={1}
            value={placement}
            onChange={(e) => setPlacement(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
          />
        </label>

        <label>
          Duration Minutes (optional)
          <input
            type="number"
            min={1}
            value={durationMinutes}
            onChange={(e) => setDurationMinutes(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
          />
        </label>

        <label>
          Notes (optional)
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
            rows={3}
          />
        </label>

        <button
          type="submit"
          disabled={submitting || loadingGames || boardGames.length === 0 || !selectedGameId}
        >
          {submitting ? "Saving..." : "Save Session"}
        </button>
      </form>
      {error && <p style={{ color: "crimson", marginBottom: 0 }}>{error}</p>}
    </section>
  );
}
