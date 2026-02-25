import { FormEvent, useEffect, useMemo, useState } from "react";

import { BoardGame, fetchBoardGames } from "../api/boardGames";
import {
  createCustomGame,
  CustomGame,
  fetchCustomGames,
  fetchFavorites,
  toggleFavorite,
} from "../api/me";
import { createSession } from "../api/sessions";

type Props = {
  onCreated: () => void;
  onCollectionChanged?: () => void;
};

type Selection =
  | { type: "global"; id: number; name: string }
  | { type: "custom"; id: number; name: string }
  | null;

export default function LogSessionForm({ onCreated, onCollectionChanged }: Props) {
  const [query, setQuery] = useState("");
  const [boardGames, setBoardGames] = useState<BoardGame[]>([]);
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [customGames, setCustomGames] = useState<CustomGame[]>([]);
  const [selection, setSelection] = useState<Selection>(null);
  const [playedDate, setPlayedDate] = useState("");
  const [playerCount, setPlayerCount] = useState(4);
  const [placement, setPlacement] = useState("");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [notes, setNotes] = useState("");
  const [loadingGames, setLoadingGames] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");

  async function loadAll() {
    setLoadingGames(true);
    setLoadError("");
    try {
      const [globalGames, favoriteRows, customRows] = await Promise.all([
        fetchBoardGames(),
        fetchFavorites(),
        fetchCustomGames(),
      ]);
      setBoardGames(globalGames);
      setFavorites(new Set(favoriteRows.map((row) => row.board_game.id)));
      setCustomGames(customRows);
      if (!selection) {
        if (customRows.length > 0) {
          setSelection({ type: "custom", id: customRows[0].id, name: customRows[0].name });
        } else if (globalGames.length > 0) {
          setSelection({ type: "global", id: globalGames[0].id, name: globalGames[0].name });
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch board games";
      setLoadError(
        `Unable to load games: ${message}. Check login state, CORS, and API base URL.`
      );
    } finally {
      setLoadingGames(false);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    const customMatches = customGames
      .filter((game) => game.name.toLowerCase().includes(q))
      .map((game) => ({ type: "custom" as const, id: game.id, name: game.name }));

    const favoriteMatches = boardGames
      .filter((game) => favorites.has(game.id))
      .filter((game) => game.name.toLowerCase().includes(q))
      .map((game) => ({ type: "global" as const, id: game.id, name: game.name }));

    const otherMatches = boardGames
      .filter((game) => !favorites.has(game.id))
      .filter((game) => game.name.toLowerCase().includes(q))
      .map((game) => ({ type: "global" as const, id: game.id, name: game.name }));

    return [...customMatches, ...favoriteMatches, ...otherMatches];
  }, [query, boardGames, customGames, favorites]);

  async function handleToggleFavorite(boardGameId: number) {
    try {
      const result = await toggleFavorite(boardGameId);
      setFavorites((prev) => {
        const next = new Set(prev);
        if (result.is_favorite) {
          next.add(boardGameId);
        } else {
          next.delete(boardGameId);
        }
        return next;
      });
      onCollectionChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle favorite");
    }
  }

  async function handleAddCustomFromQuery() {
    const name = query.trim();
    if (!name) return;
    try {
      const created = await createCustomGame(name);
      setCustomGames((prev) => [created, ...prev]);
      setSelection({ type: "custom", id: created.id, name: created.name });
      setError("");
      onCollectionChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add custom game");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!selection) {
      setError("Please select a game");
      return;
    }
    if (!/^\d{2}\/\d{2}\/\d{4}$/.test(playedDate)) {
      setError("played_date must be MM/DD/YYYY");
      return;
    }

    setSubmitting(true);
    try {
      await createSession({
        board_game_id: selection.type === "global" ? selection.id : undefined,
        user_custom_game_id: selection.type === "custom" ? selection.id : undefined,
        played_date: playedDate,
        player_count: Number(playerCount),
        placement: placement ? Number(placement) : undefined,
        duration_minutes: durationMinutes ? Number(durationMinutes) : undefined,
        notes: notes || undefined,
      });
      setPlayedDate("");
      setPlayerCount(4);
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
    <section className="panel">
      <h2 className="panel-title">Log Session</h2>
      {loadError && <p className="error-text" style={{ marginBottom: 10 }}>{loadError}</p>}
      <form onSubmit={handleSubmit} className="form-grid">
        <label className="field">
          Search board game
          <input
            type="text"
            placeholder="Search board game..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loadingGames}
            className="input"
          />
        </label>

        <p className="meta-text">
          <strong>Selected:</strong> {selection ? selection.name : "None"}
        </p>

        <div className="search-list">
          {filteredResults.map((item) => {
            const isSelected = selection?.type === item.type && selection.id === item.id;
            const isGlobal = item.type === "global";
            const isFav = isGlobal && favorites.has(item.id);
            return (
              <div key={`${item.type}-${item.id}`} style={{ display: "flex", alignItems: "center" }}>
                <button
                  type="button"
                  onClick={() => setSelection(item)}
                  className={`search-item ${isSelected ? "active" : ""}`}
                  style={{ flex: 1 }}
                >
                  {item.name}
                </button>
                {isGlobal && (
                  <button
                    type="button"
                    onClick={() => void handleToggleFavorite(item.id)}
                    title={isFav ? "Unfavorite" : "Favorite"}
                    style={{
                      border: 0,
                      background: "transparent",
                      cursor: "pointer",
                      padding: "0 10px",
                      fontSize: "1.1rem",
                    }}
                  >
                    {isFav ? "⭐" : "☆"}
                  </button>
                )}
              </div>
            );
          })}
          {filteredResults.length === 0 && (
            <div style={{ padding: 10 }}>
              <p className="meta-text" style={{ marginBottom: 8 }}>
                No matching board games.
              </p>
              {query.trim() && (
                <button type="button" className="btn" onClick={() => void handleAddCustomFromQuery()}>
                  Add as custom game
                </button>
              )}
            </div>
          )}
        </div>

        <label className="field">
          Played date
          <input
            type="text"
            placeholder="MM/DD/YYYY"
            value={playedDate}
            onChange={(e) => setPlayedDate(e.target.value)}
            className="input"
            required
          />
        </label>

        <label className="field">
          Player count
          <input
            type="number"
            min={1}
            value={playerCount}
            onChange={(e) => setPlayerCount(Number(e.target.value))}
            className="input"
            required
          />
        </label>

        <label className="field">
          Placement (optional)
          <input
            type="number"
            min={1}
            value={placement}
            onChange={(e) => setPlacement(e.target.value)}
            className="input"
          />
        </label>

        <label className="field">
          Duration minutes (optional)
          <input
            type="number"
            min={1}
            value={durationMinutes}
            onChange={(e) => setDurationMinutes(e.target.value)}
            className="input"
          />
        </label>

        <label className="field">
          Notes (optional)
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="textarea"
          />
        </label>

        <button type="submit" className="btn" disabled={submitting || loadingGames || !selection}>
          {submitting ? "Saving..." : "Save Session"}
        </button>
      </form>
      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
    </section>
  );
}
