import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BoardGameSearchItem, searchBoardGames } from "../api/boardGames";
import { createCustomGame, toggleFavorite } from "../api/me";
import { createSession } from "../api/sessions";

type Props = {
  onCreated: () => void;
  onCollectionChanged?: () => void;
};

export default function LogSessionForm({ onCreated, onCollectionChanged }: Props) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<BoardGameSearchItem[]>([]);
  const [selectedGame, setSelectedGame] = useState<BoardGameSearchItem | null>(null);
  const [playedDate, setPlayedDate] = useState("");
  const [playerCount, setPlayerCount] = useState(4);
  const [placement, setPlacement] = useState("");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [notes, setNotes] = useState("");
  const [loadingGames, setLoadingGames] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadSearch(query);
    }, 250);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  async function loadSearch(searchTerm: string) {
    setLoadingGames(true);
    setLoadError("");
    try {
      const items = await searchBoardGames(searchTerm);
      setResults(items);
      if (!selectedGame && items.length > 0) {
        setSelectedGame(items[0]);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch board games";
      if (message.includes("(401)") || message.toLowerCase().includes("credential")) {
        navigate("/login", { replace: true });
        return;
      }
      setLoadError(
        `Unable to load games: ${message}. Check auth, CORS, and VITE_API_BASE_URL.`
      );
      setResults([]);
    } finally {
      setLoadingGames(false);
    }
  }

  async function handleToggleFavorite(item: BoardGameSearchItem) {
    if (item.source !== "global") {
      return;
    }
    try {
      const result = await toggleFavorite(item.id);
      setResults((prev) =>
        prev.map((it) =>
          it.source === "global" && it.id === item.id
            ? { ...it, is_favorite: result.is_favorite }
            : it
        )
      );
      onCollectionChanged?.();
      void loadSearch(query);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle favorite");
    }
  }

  async function handleAddCustomFromQuery() {
    const name = query.trim();
    if (!name) return;
    try {
      const created = await createCustomGame(name);
      const custom: BoardGameSearchItem = {
        key: `custom:${created.id}`,
        id: created.id,
        name: created.name,
        source: "custom",
        is_favorite: false,
      };
      setSelectedGame(custom);
      setResults((prev) => [custom, ...prev]);
      setError("");
      onCollectionChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add custom game");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!selectedGame) {
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
        board_game_id: selectedGame.source === "global" ? selectedGame.id : undefined,
        user_custom_game_id: selectedGame.source === "custom" ? selectedGame.id : undefined,
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

  const hasResults = useMemo(() => results.length > 0, [results]);

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
          <strong>Selected:</strong> {selectedGame ? selectedGame.name : "None"}
        </p>

        <div className="search-list">
          {hasResults &&
            results.map((item) => {
              const isSelected = selectedGame?.key === item.key;
              return (
                <div key={item.key} style={{ display: "flex", alignItems: "center" }}>
                  <button
                    type="button"
                    onClick={() => setSelectedGame(item)}
                    className={`search-item ${isSelected ? "active" : ""}`}
                    style={{ flex: 1 }}
                  >
                    {item.name}
                    <span className="meta-text" style={{ marginLeft: 8 }}>
                      ({item.source})
                    </span>
                  </button>
                  {item.source === "global" && (
                    <button
                      type="button"
                      onClick={() => void handleToggleFavorite(item)}
                      title={item.is_favorite ? "Unfavorite" : "Favorite"}
                      style={{
                        border: 0,
                        background: "transparent",
                        cursor: "pointer",
                        padding: "0 10px",
                        fontSize: "1.1rem",
                      }}
                    >
                      {item.is_favorite ? "⭐" : "☆"}
                    </button>
                  )}
                </div>
              );
            })}

          {!hasResults && !loadingGames && (
            <div style={{ padding: 10 }}>
              <p className="meta-text" style={{ marginBottom: 8 }}>
                No matching board games.
              </p>
              {query.trim() && (
                <button
                  type="button"
                  className="btn"
                  onClick={() => void handleAddCustomFromQuery()}
                >
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
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="textarea" />
        </label>

        <button type="submit" className="btn" disabled={submitting || loadingGames || !selectedGame}>
          {submitting ? "Saving..." : "Save Session"}
        </button>
      </form>
      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
    </section>
  );
}
