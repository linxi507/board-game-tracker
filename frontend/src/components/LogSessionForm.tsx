import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BoardGame, fetchBoardGames } from "../api/boardGames";
import {
  addFavorite,
  createCustomGame,
  CustomGame,
  fetchCustomGames,
  fetchFavorites,
  removeFavorite,
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

const PAGE_SIZE = 20;

export default function LogSessionForm({ onCreated, onCollectionChanged }: Props) {
  const navigate = useNavigate();
  const searchContainerRef = useRef<HTMLDivElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedTerm = useDebouncedValue(searchTerm, 250);
  const [globalGames, setGlobalGames] = useState<BoardGame[]>([]);
  const [globalTotal, setGlobalTotal] = useState(0);
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set());
  const [customGames, setCustomGames] = useState<CustomGame[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [selectedGame, setSelectedGame] = useState<Suggestion | null>(null);
  const [playedDate, setPlayedDate] = useState("");
  const [playerCount, setPlayerCount] = useState(4);
  const [placement, setPlacement] = useState("");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [notes, setNotes] = useState("");
  const [loadingGames, setLoadingGames] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const listboxId = "game-search-listbox";

  const suggestions = useMemo(() => {
    const q = debouncedTerm.trim().toLowerCase();
    const customItems = customGames
      .filter((item) => item.name.toLowerCase().includes(q))
      .map<Suggestion>((item) => ({
        key: `custom:${item.id}`,
        id: item.id,
        name: item.name,
        source: "custom",
        isFavorite: false,
      }));

    const favoriteGlobals = globalGames
      .filter((game) => favoriteIds.has(game.id))
      .map<Suggestion>((game) => ({
        key: `global:${game.id}`,
        id: game.id,
        name: game.name,
        source: "global",
        isFavorite: true,
      }));

    const otherGlobals = globalGames
      .filter((game) => !favoriteIds.has(game.id))
      .map<Suggestion>((game) => ({
        key: `global:${game.id}`,
        id: game.id,
        name: game.name,
        source: "global",
        isFavorite: false,
      }));

    return [...customItems, ...favoriteGlobals, ...otherGlobals];
  }, [customGames, debouncedTerm, favoriteIds, globalGames]);

  const hasMoreGlobalGames = globalGames.length < globalTotal;

  function isAuthError(message: string): boolean {
    return (
      message.includes("(401)") ||
      message.includes("(403)") ||
      message.toLowerCase().includes("not authenticated")
    );
  }

  async function loadInitialResults(term: string) {
    setLoadingGames(true);
    setLoadError("");
    try {
      const [boardGamesPage, favoriteRows, customRows] = await Promise.all([
        fetchBoardGames(term, PAGE_SIZE, 0),
        fetchFavorites(),
        fetchCustomGames(),
      ]);

      setGlobalGames(boardGamesPage.items);
      setGlobalTotal(boardGamesPage.total);
      setFavoriteIds(new Set(favoriteRows.map((row) => row.board_game.id)));
      setCustomGames(customRows);
      setActiveIndex(0);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load board games";
      console.error("Failed to load board games", err);
      if (isAuthError(message)) {
        navigate("/login", { replace: true });
        return;
      }
      setLoadError("Failed to load games. Please refresh and try again.");
      setGlobalGames([]);
      setGlobalTotal(0);
    } finally {
      setLoadingGames(false);
    }
  }

  useEffect(() => {
    void loadInitialResults(debouncedTerm);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedTerm, navigate]);

  useEffect(() => {
    setSelectedGame((previous) => {
      if (!previous) return suggestions[0] ?? null;
      const stillPresent = suggestions.find((item) => item.key === previous.key);
      return stillPresent ?? previous;
    });
    setActiveIndex((previous) => {
      if (suggestions.length === 0) return 0;
      if (previous > suggestions.length - 1) return suggestions.length - 1;
      return previous;
    });
  }, [suggestions]);

  useEffect(() => {
    if (!import.meta.env.DEV) return;
    const renderedGlobalCount = suggestions.filter((item) => item.source === "global").length;
    if (renderedGlobalCount !== globalGames.length) {
      console.warn("Suggestion/global count mismatch", {
        renderedGlobalCount,
        globalGamesCount: globalGames.length,
      });
    }
  }, [globalGames.length, suggestions]);

  useEffect(() => {
    function handleDocumentClick(event: MouseEvent) {
      if (!searchContainerRef.current) return;
      if (!searchContainerRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }

    document.addEventListener("mousedown", handleDocumentClick);
    return () => document.removeEventListener("mousedown", handleDocumentClick);
  }, []);

  function selectSuggestion(item: Suggestion) {
    setSelectedGame(item);
    setSearchTerm(item.name);
    setDropdownOpen(false);
  }

  const loadMoreGlobalGames = useCallback(async () => {
    if (loadingMore || !hasMoreGlobalGames) return;
    setLoadingMore(true);
    try {
      const nextPage = await fetchBoardGames(debouncedTerm, PAGE_SIZE, globalGames.length);
      setGlobalGames((previous) => {
        const seen = new Set(previous.map((item) => item.id));
        const merged = [...previous];
        for (const item of nextPage.items) {
          if (!seen.has(item.id)) {
            merged.push(item);
          }
        }
        return merged;
      });
      setGlobalTotal(nextPage.total);
    } catch (err) {
      console.error("Failed to load more board games", err);
      setLoadError("Failed to load games. Please refresh and try again.");
    } finally {
      setLoadingMore(false);
    }
  }, [debouncedTerm, globalGames.length, hasMoreGlobalGames, loadingMore]);

  useEffect(() => {
    const element = listRef.current;
    if (!element) return;

    function onScroll() {
      const currentElement = listRef.current;
      if (!currentElement || loadingMore || loadingGames || !hasMoreGlobalGames) return;
      const nearBottom =
        currentElement.scrollTop + currentElement.clientHeight >= currentElement.scrollHeight - 24;
      if (nearBottom) {
        void loadMoreGlobalGames();
      }
    }

    element.addEventListener("scroll", onScroll);
    return () => element.removeEventListener("scroll", onScroll);
  }, [hasMoreGlobalGames, loadMoreGlobalGames, loadingGames, loadingMore]);

  async function handleToggleFavorite(item: Suggestion) {
    if (item.source !== "global") return;

    setError("");
    const wasFavorite = favoriteIds.has(item.id);
    const nextIds = new Set(favoriteIds);
    if (wasFavorite) nextIds.delete(item.id);
    else nextIds.add(item.id);
    setFavoriteIds(nextIds);

    try {
      if (wasFavorite) await removeFavorite(item.id);
      else await addFavorite(item.id);
      onCollectionChanged?.();
    } catch (err) {
      setFavoriteIds(favoriteIds);
      setError(err instanceof Error ? err.message : "Failed to update favorite");
    }
  }

  async function handleAddCustomGame() {
    const name = searchTerm.trim();
    if (!name) return;

    try {
      const created = await createCustomGame(name);
      setCustomGames((previous) => [created, ...previous]);
      const createdSuggestion: Suggestion = {
        key: `custom:${created.id}`,
        id: created.id,
        name: created.name,
        source: "custom",
        isFavorite: false,
      };
      setSelectedGame(createdSuggestion);
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
      setActiveIndex((previous) => (previous + 1) % suggestions.length);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((previous) => (previous - 1 + suggestions.length) % suggestions.length);
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
        <div ref={searchContainerRef}>
          <label className="field">
            Search board game
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => {
                setSearchTerm(event.target.value);
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
          </label>

          {dropdownOpen && (
            <div ref={listRef} className="search-list" id={listboxId} role="listbox">
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
                    </button>
                    {item.source === "global" && (
                      <button
                        type="button"
                        className={`star-btn ${item.isFavorite ? "star-btn-active" : ""}`}
                        onClick={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          void handleToggleFavorite(item);
                        }}
                        title={item.isFavorite ? "Remove favorite" : "Add favorite"}
                      >
                        {item.isFavorite ? "\u2605" : "\u2606"}
                      </button>
                    )}
                  </div>
                ))}

              {!loadingGames && !suggestions.length && (
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

              {!loadingGames && hasMoreGlobalGames && (
                <div className="search-footer">
                  <button
                    type="button"
                    className="search-load-more"
                    onClick={() => void loadMoreGlobalGames()}
                    disabled={loadingMore}
                  >
                    {loadingMore ? "Loading..." : "Load more"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

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
            onChange={(event) => setPlayedDate(event.target.value)}
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
            onChange={(event) => setPlayerCount(Number(event.target.value))}
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
            onChange={(event) => setPlacement(event.target.value)}
          />
        </label>

        <label className="field">
          Duration minutes (optional)
          <input
            type="number"
            min={1}
            className="input"
            value={durationMinutes}
            onChange={(event) => setDurationMinutes(event.target.value)}
          />
        </label>

        <label className="field">
          Notes (optional)
          <textarea className="textarea" value={notes} onChange={(event) => setNotes(event.target.value)} />
        </label>

        <button type="submit" className="btn" disabled={submitting || !selectedGame}>
          {submitting ? "Saving..." : "Save Session"}
        </button>
      </form>
      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
    </section>
  );
}
