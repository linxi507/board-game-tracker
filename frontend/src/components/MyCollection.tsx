import { useEffect, useState } from "react";

import { deleteCustomGame, fetchCustomGames, fetchFavorites } from "../api/me";

type Props = {
  reloadSignal: number;
};

export default function MyCollection({ reloadSignal }: Props) {
  const [favoriteNames, setFavoriteNames] = useState<string[]>([]);
  const [customGames, setCustomGames] = useState<Array<{ id: number; name: string }>>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    async function loadCollection() {
      setLoading(true);
      setError("");
      try {
        const [favorites, custom] = await Promise.all([fetchFavorites(), fetchCustomGames()]);
        setFavoriteNames(favorites.map((item) => item.board_game.name));
        setCustomGames(custom.map((item) => ({ id: item.id, name: item.name })));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load collection");
      } finally {
        setLoading(false);
      }
    }

    void loadCollection();
  }, [reloadSignal]);

  async function handleDeleteCustomGame(customGameId: number) {
    const confirmed = window.confirm("Delete this custom game? This cannot be undone.");
    if (!confirmed) return;

    setError("");
    setDeletingId(customGameId);
    try {
      await deleteCustomGame(customGameId);
      setCustomGames((previous) => previous.filter((item) => item.id !== customGameId));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete custom game";
      if (message.includes("Cannot delete: custom game is used by sessions")) {
        setError("Cannot delete custom game because it is used by existing sessions.");
      } else {
        setError(message);
      }
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="panel">
      <h2 className="panel-title">My Collection</h2>
      {loading && <p>Loading collection...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && (
        <div className="stats-grid">
          <div className="stats-item">
            <p className="stats-label">Favorites</p>
            {favoriteNames.length === 0 && <p className="meta-text">None yet</p>}
            {favoriteNames.length > 0 && (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {favoriteNames.map((name) => (
                  <li key={`fav-${name}`}>{name}</li>
                ))}
              </ul>
            )}
          </div>
          <div className="stats-item">
            <p className="stats-label">Custom Games</p>
            {customGames.length === 0 && <p className="meta-text">None yet</p>}
            {customGames.length > 0 && (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {customGames.map((game) => (
                  <li
                    key={`custom-${game.id}`}
                    style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
                  >
                    <span>{game.name}</span>
                    <button
                      type="button"
                      title="Delete custom game"
                      onClick={() => void handleDeleteCustomGame(game.id)}
                      disabled={deletingId === game.id}
                      style={{
                        border: "none",
                        background: "transparent",
                        cursor: "pointer",
                        color: "#8a2f2f",
                        fontSize: "0.95rem",
                      }}
                    >
                      {deletingId === game.id ? "..." : "Delete"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
