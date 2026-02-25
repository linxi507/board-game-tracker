import { useEffect, useState } from "react";

import { fetchCustomGames, fetchFavorites } from "../api/me";

type Props = {
  reloadSignal: number;
};

export default function MyCollection({ reloadSignal }: Props) {
  const [favoriteNames, setFavoriteNames] = useState<string[]>([]);
  const [customNames, setCustomNames] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCollection() {
      setLoading(true);
      setError("");
      try {
        const [favorites, custom] = await Promise.all([fetchFavorites(), fetchCustomGames()]);
        setFavoriteNames(favorites.map((item) => item.board_game.name));
        setCustomNames(custom.map((item) => item.name));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load collection");
      } finally {
        setLoading(false);
      }
    }

    void loadCollection();
  }, [reloadSignal]);

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
            {customNames.length === 0 && <p className="meta-text">None yet</p>}
            {customNames.length > 0 && (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {customNames.map((name) => (
                  <li key={`custom-${name}`}>{name}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
