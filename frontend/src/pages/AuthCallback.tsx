import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect } from "react";

import { setToken } from "../api/client";

export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const error = searchParams.get("error");

  useEffect(() => {
    if (!token) {
      return;
    }
    setToken(token);
    navigate("/dashboard", { replace: true });
  }, [navigate, token]);

  return (
    <main className="auth-shell">
      <h1 className="auth-title">Google Sign-In</h1>
      {!token && (
        <>
          <p className="auth-subtitle">
            {error ?? "Missing sign-in token."}
          </p>
          <p className="meta-text">
            Return to <Link to="/login">Login</Link>
          </p>
        </>
      )}
      {token && <p className="auth-subtitle">Signing you in...</p>}
    </main>
  );
}
