import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { login, register } from "../api/auth";
import { setToken } from "../api/client";

const USERNAME_REGEX = /^[A-Za-z0-9]+$/;
const PASSWORD_REGEX = /^[A-Za-z0-9]+$/;

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!USERNAME_REGEX.test(username) || username.length < 3 || username.length > 20) {
      setError("Username must be 3-20 alphanumeric characters");
      return;
    }
    if (!PASSWORD_REGEX.test(password) || password.length < 8 || password.length > 72) {
      setError("Password must be 8-72 characters and contain only letters and digits");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await register({ username, email, password });
      const token = await login({ identifier: username, password });
      setToken(token.access_token);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <h1 className="auth-title">Create Account</h1>
      <p className="auth-subtitle">Build your board game profile in seconds.</p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label className="field">
          Username
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="input"
          />
        </label>
        <label className="field">
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
        <label className="field">
          Confirm Password
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="input"
          />
        </label>
        <button type="submit" disabled={loading} className="btn">
          {loading ? "Creating account..." : "Create Account"}
        </button>
      </form>
      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
      <p className="meta-text" style={{ marginTop: 12 }}>
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </main>
  );
}
