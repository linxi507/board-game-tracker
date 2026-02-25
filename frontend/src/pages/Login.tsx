import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { login } from "../api/auth";
import { setToken } from "../api/client";

export default function Login() {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await login({ identifier, password });
      setToken(response.access_token);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <h1 className="auth-title">Sign In</h1>
      <p className="auth-subtitle">Track every board game night in one place.</p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label className="field">
          Email or Username
          <input
            type="text"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
            className="input"
          />
        </label>

        <label className="field">
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="input"
          />
        </label>

        <button type="submit" disabled={loading} className="btn">
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
      <p className="meta-text" style={{ marginTop: 12 }}>
        No account? <Link to="/register">Register</Link>
      </p>
    </main>
  );
}
