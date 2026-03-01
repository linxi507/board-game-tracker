import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BoardGame, fetchBoardGames } from "../api/boardGames";
import { addFavorite, createCustomGame, removeFavorite } from "../api/me";
import { createSession } from "../api/sessions";
import { useDebouncedValue } from "../hooks/useDebouncedValue";

type Props = {
  onCreated: () => void;
  onCollectionChanged?: () => void;
  reloadSignal: number;
};

type Suggestion = {
  key: string;
  id: number;
  name: string;
  source: "global" | "custom";
  isFavorite: boolean;
};

const PAGE_SIZE = 50;

function StarIcon({ active }: { active: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="18"
      height="18"
      aria-hidden="true"
      className="star-icon"
      fill={active ? "#fbbf24" : "none"}
      stroke={active ? "#f59e0b" : "#97a39b"}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 3.8l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 17l-5.2 2.8 1-5.8-4.2-4.1 5.8-.8L12 3.8z" />
    </svg>
  );
}

export default function LogSessionForm({ onCreated, onCollectionChanged, reloadSignal }: Props) {
  const navigate = useNavigate();
  const searchContainerRef = useRef<HTMLDivElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedTerm = useDebouncedValue(searchTerm, 250);
  const [games, setGames] = useState<BoardGame[]>([]);
  const [total, setTotal] = useState(0);
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
    const mapped = games.map<Suggestion>((item) => ({
      key: item.key,
      id: item.id,
      name: item.name,
      source: item.source,
      isFavorite: item.is_favorite,
    }));
    const favorites = mapped.filter((item) => item.source === "global" && item.isFavorite);
    const rest = mapped.filter((item) => !(item.source === "global" && item.isFavorite));
    return [...favorites, ...rest];
  }, [games]);

  const hasMore = games.length < total;

  function isAuthError(message: string): boolean {
    return (
      message.includes("(401)") ||
      message.includes("(403)") ||
      message.toLowerCase().includes("not authenticated")
    );
  }

  async function loadInitial(term: string) {
    setLoadingGames(true);
    setLoadError("");
    try {
      const page = await fetchBoardGames(term, PAGE_SIZE, 0);
      setGames(page.items);
      setTotal(page.total);
      setActiveIndex(0);
      if (import.meta.env.DEV) {
        console.debug("board-games api/render count", {
          apiItems: page.items.length,
          renderedItems: page.items.length,
          limit: PAGE_SIZE,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load board games";
      console.error("Failed to load board games", err);
      if (isAuthError(message)) {
        navigate("/login", { replace: true });
        return;
      }
      setLoadError("Failed to load games. Please refresh and try again.");
      setGames([]);
      setTotal(0);
    } finally {
      setLoadingGames(false);
    }
  }

  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const page = await fetchBoardGames(debouncedTerm, PAGE_SIZE, games.length);
      setGames((previous) => {
        const seen = new Set(previous.map((item) => item.key));
        const merged = [...previous];
        for (const item of page.items) {
          if (!seen.has(item.key)) merged.push(item);
        }
        return merged;
      });
      setTotal(page.total);
    } catch (err) {
      console.error("Failed to load more board games", err);
      setLoadError("Failed to load games. Please refresh and try again.");
    } finally {
      setLoadingMore(false);
    }
  }, [debouncedTerm, games.length, hasMore, loadingMore]);

  useEffect(() => {
    void loadInitial(debouncedTerm);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedTerm, reloadSignal, navigate]);

  useEffect(() => {
    setSelectedGame((previous) => {
      if (!previous) return suggestions[0] ?? null;
      return suggestions.find((item) => item.key === previous.key) ?? previous;
    });
    setActiveIndex((previous) => {
      if (suggestions.length === 0) return 0;
      return Math.min(previous, suggestions.length - 1);
    });
  }, [suggestions]);

  useEffect(() => {
    function handleDocumentClick(event: MouseEvent) {
      if (!searchContainerRef.current) return;
      if (!searchContainerRef.current.contains(event.target as Node)) setDropdownOpen(false);
    }
    document.addEventListener("mousedown", handleDocumentClick);
    return () => document.removeEventListener("mousedown", handleDocumentClick);
  }, []);

  useEffect(() => {
    const element = listRef.current;
    if (!element) return;
    function onScroll() {
      const current = listRef.current;
      if (!current || loadingMore || loadingGames || !hasMore) return;
      const nearBottom = current.scrollTop + current.clientHeight >= current.scrollHeight - 24;
      if (nearBottom) void loadMore();
    }
    element.addEventListener("scroll", onScroll);
    return () => element.removeEventListener("scroll", onScroll);
  }, [hasMore, loadMore, loadingGames, loadingMore]);

  function selectSuggestion(item: Suggestion) {
    setSelectedGame(item);
    setSearchTerm(item.name);
    setDropdownOpen(false);
  }

  async function handleToggleFavorite(item: Suggestion) {
    if (item.source !== "global") return;
    setError("");
    const nextFavorite = !item.isFavorite;
    setGames((previous) =>
      previous.map((row) => (row.key === item.key ? { ...row, is_favorite: nextFavorite } : row))
    );
    try {
      if (nextFavorite) await addFavorite(item.id);
      else await removeFavorite(item.id);
      onCollectionChanged?.();
    } catch (err) {
      setGames((previous) =>
        previous.map((row) => (row.key === item.key ? { ...row, is_favorite: item.isFavorite } : row))
      );
      setError(err instanceof Error ? err.message : "Failed to update favorite");
    }
  }

  async function handleAddCustomGame() {
    const name = searchTerm.trim();
    if (!name) return;
    try {
      const created = await createCustomGame(name);
      setGames((previous) => [
        {
          key: `custom:${created.id}`,
          id: created.id,
          name: created.name,
          source: "custom",
          is_favorite: false,
        },
        ...previous,
      ]);
      setTotal((value) => value + 1);
      setSelectedGame({
        key: `custom:${created.id}`,
        id: created.id,
        name: created.name,
        source: "custom",
        isFavorite: false,
      });
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
    if (event.key === "Tab") setDropdownOpen(false);
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
                        <StarIcon active={item.isFavorite} />
                      </button>
                    )}
                  </div>
                ))}
              {!loadingGames && suggestions.length === 0 && (
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
              {!loadingGames && hasMore && (
                <div className="search-footer">
                  <button
                    type="button"
                    className="search-load-more"
                    onClick={() => void loadMore()}
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
