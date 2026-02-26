import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BoardGame, fetchBoardGames } from "../api/boardGames";
import {
  createCustomGame,
  CustomGame,
  fetchCustomGames,
  fetchFavorites,
  toggleFavorite,
} from "../api/me";
import { createSession } from "../api/sessions";
import { useDebouncedValue } from "../hooks/useDebouncedValue";

type Props = {
  onCreated: () => void;
  onCollectionChanged?: () => void;
};

type Suggestion = {
  key: string;
  id: number;
  name: string;
  source: "global" | "custom";
  isFavorite: boolean;
};

export default function LogSessionForm({ onCreated, onCollectionChanged }: Props) {
  const navigate = useNavigate();
  const searchContainerRef = useRef<HTMLDivElement | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedTerm = useDebouncedValue(searchTerm, 250);
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set());
  const [customGames, setCustomGames] = useState<CustomGame[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [selectedGame, setSelectedGame] = useState<Suggestion | null>(null);
  const [playedDate, setPlayedDate] = useState("");
  const [playerCount, setPlayerCount] = useState(4);
  const [placement, setPlacement] = useState("");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [notes, setNotes] = useState("");
  const [loadingGames, setLoadingGames] = useState(true);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const listboxId = "game-search-listbox";

  function isAuthError(message: string): boolean {
    return (
      message.includes("(401)") ||
      message.includes("(403)") ||
      message.toLowerCase().includes("not authenticated")
    );
  }

  function buildSuggestions(
    globals: BoardGame[],
    favorites: Set<number>,
    custom: CustomGame[],
    term: string
  ): Suggestion[] {
    const q = term.trim().toLowerCase();
    const customItems = custom
      .filter((item) => item.name.toLowerCase().includes(q))
      .map<Suggestion>((item) => ({
        key: `custom:${item.id}`,
        id: item.id,
        name: item.name,
        source: "custom",
        isFavorite: false,
      }));

    const favoriteGlobal = globals
      .filter((game) => favorites.has(game.id))
      .map<Suggestion>((game) => ({
        key: `global:${game.id}`,
        id: game.id,
        name: game.name,
        source: "global",
        isFavorite: true,
      }));

    const nonFavoriteGlobal = globals
      .filter((game) => !favorites.has(game.id))
      .map<Suggestion>((game) => ({
        key: `global:${game.id}`,
        id: game.id,
        name: game.name,
        source: "global",
        isFavorite: false,
      }));

    const merged = [...customItems, ...favoriteGlobal, ...nonFavoriteGlobal];
    const deduped: Suggestion[] = [];
    const seen = new Set<string>();
    for (const item of merged) {
      if (seen.has(item.key)) {
        continue;
      }
      seen.add(item.key);
      deduped.push(item);
    }
    return deduped;
  }

  useEffect(() => {
    let isCancelled = false;

    async function loadSuggestions() {
      setLoadingGames(true);
      setLoadError("");
      try {
        const [globalPage, favoriteRows, customRows] = await Promise.all([
          fetchBoardGames(debouncedTerm, 20, 0),
          fetchFavorites(),
          fetchCustomGames(),
        ]);

        if (isCancelled) {
          return;
        }

        const favorites = new Set(favoriteRows.map((row) => row.board_game.id));
        const built = buildSuggestions(globalPage.items, favorites, customRows, debouncedTerm);

        setFavoriteIds(favorites);
        setCustomGames(customRows);
        setSuggestions(built.slice(0, 20));
        setActiveIndex(0);
        setSelectedGame((prev) => prev ?? built[0] ?? null);
      } catch (err) {
        if (isCancelled) {
          return;
        }

        const message = err instanceof Error ? err.message : "Failed to load board games";
        if (isAuthError(message)) {
          navigate("/login", { replace: true });
          return;
        }

        setLoadError(`Unable to load games: ${message}. Check API URL/auth/CORS and try again.`);
        setSuggestions([]);
      } finally {
        if (!isCancelled) {
          setLoadingGames(false);
        }
      }
    }

    void loadSuggestions();

    return () => {
      isCancelled = true;
    };
  }, [debouncedTerm, navigate]);

  useEffect(() => {
    function handleDocumentClick(event: MouseEvent) {
      if (!searchContainerRef.current) {
        return;
      }
      if (!searchContainerRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }

    document.addEventListener("mousedown", handleDocumentClick);
    return () => {
      document.removeEventListener("mousedown", handleDocumentClick);
    };
  }, []);

  const hasSuggestions = useMemo(() => suggestions.length > 0, [suggestions]);

  function selectSuggestion(item: Suggestion) {
    setSelectedGame(item);
    setSearchTerm(item.name);
    setDropdownOpen(false);
  }

  async function handleToggleFavorite(item: Suggestion) {
    if (item.source !== "global") {
      return;
    }
    try {
      const result = await toggleFavorite(item.id);
      const nextFavorites = new Set(favoriteIds);
      if (result.is_favorite) {
        nextFavorites.add(item.id);
      } else {
        nextFavorites.delete(item.id);
      }
      setFavoriteIds(nextFavorites);
      onCollectionChanged?.();

      const refreshed = await fetchBoardGames(debouncedTerm, 20, 0);
      const rebuilt = buildSuggestions(refreshed.items, nextFavorites, customGames, debouncedTerm);
      setSuggestions(rebuilt.slice(0, 20));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle favorite");
    }
  }

  async function handleAddCustomGame() {
    const name = searchTerm.trim();
    if (!name) {
      return;
    }

    try {
      const created = await createCustomGame(name);
      const nextCustom = [created, ...customGames];
      setCustomGames(nextCustom);

      const customSuggestion: Suggestion = {
        key: `custom:${created.id}`,
        id: created.id,
        name: created.name,
        source: "custom",
        isFavorite: false,
      };

      setSelectedGame(customSuggestion);
      setSuggestions([customSuggestion, ...suggestions].slice(0, 20));
      setDropdownOpen(false);
      onCollectionChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add custom game");
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!dropdownOpen || suggestions.length === 0) {
      if (event.key === "ArrowDown" && suggestions.length > 0) {
        event.preventDefault();
        setDropdownOpen(true);
        setActiveIndex(0);
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((prev) => (prev + 1) % suggestions.length);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
      return;
    }

    if (event.key === "Enter" && suggestions[activeIndex]) {
      event.preventDefault();
      selectSuggestion(suggestions[activeIndex]);
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      setDropdownOpen(false);
      return;
    }

    if (event.key === "Tab") {
      setDropdownOpen(false);
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

  return (
    <section className="panel">
      <h2 className="panel-title">Log Session</h2>
      {loadError && (
        <p className="error-text" style={{ marginBottom: 10 }}>
          {loadError}
        </p>
      )}

      <form onSubmit={handleSubmit} className="form-grid">
        <label className="field">
          Search board game
          <div ref={searchContainerRef}>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setDropdownOpen(true);
              }}
              onFocus={() => setDropdownOpen(true)}
              onKeyDown={handleKeyDown}
              className="input"
              placeholder="Type to search..."
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={dropdownOpen}
              aria-controls={listboxId}
              aria-activedescendant={
                dropdownOpen && suggestions[activeIndex] ? `${listboxId}-${activeIndex}` : undefined
              }
            />
          </div>
        </label>

        {dropdownOpen && (
          <div className="search-list" id={listboxId} role="listbox">
            {loadingGames && (
              <div style={{ padding: 10 }} className="meta-text">
                Loading...
              </div>
            )}

            {!loadingGames &&
              suggestions.map((item, index) => (
                <div
                  key={item.key}
                  id={`${listboxId}-${index}`}
                  role="option"
                  aria-selected={activeIndex === index}
                  style={{ display: "flex", alignItems: "center" }}
                >
                  <button
                    type="button"
                    className={`search-item ${activeIndex === index ? "active" : ""}`}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => selectSuggestion(item)}
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
                      onClick={(e) => {
                        e.preventDefault();
                        void handleToggleFavorite(item);
                      }}
                      title={item.isFavorite ? "Unfavorite" : "Favorite"}
                      style={{
                        border: 0,
                        background: "transparent",
                        cursor: "pointer",
                        padding: "0 10px",
                        fontSize: "1.1rem",
                      }}
                    >
                      {item.isFavorite ? "\u2605" : "\u2606"}
                    </button>
                  )}
                </div>
              ))}

            {!loadingGames && !hasSuggestions && (
              <div style={{ padding: 10 }}>
                <p className="meta-text" style={{ marginBottom: 8 }}>
                  No matching board games.
                </p>
                {searchTerm.trim() && (
                  <button type="button" className="btn" onClick={() => void handleAddCustomGame()}>
                    Add as custom game
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        <p className="meta-text">
          <strong>Selected:</strong> {selectedGame ? selectedGame.name : "None"}
        </p>

        <label className="field">
          Played date
          <input
            type="text"
            className="input"
            placeholder="MM/DD/YYYY"
            value={playedDate}
            onChange={(e) => setPlayedDate(e.target.value)}
            required
          />
        </label>

        <label className="field">
          Player count
          <input
            type="number"
            min={1}
            className="input"
            value={playerCount}
            onChange={(e) => setPlayerCount(Number(e.target.value))}
            required
          />
        </label>

        <label className="field">
          Placement (optional)
          <input
            type="number"
            min={1}
            className="input"
            value={placement}
            onChange={(e) => setPlacement(e.target.value)}
          />
        </label>

        <label className="field">
          Duration minutes (optional)
          <input
            type="number"
            min={1}
            className="input"
            value={durationMinutes}
            onChange={(e) => setDurationMinutes(e.target.value)}
          />
        </label>

        <label className="field">
          Notes (optional)
          <textarea className="textarea" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>

        <button type="submit" className="btn" disabled={submitting || !selectedGame}>
          {submitting ? "Saving..." : "Save Session"}
        </button>
      </form>

      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
    </section>
  );
}
