import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch, getToken } from "../api/client";
import LogSessionForm from "../components/LogSessionForm";
import SessionsList from "../components/SessionsList";
import StatsPanel from "../components/StatsPanel";

type MeResponse = {
  id: number;
  email: string;
  created_at: string;
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [reloadCounter, setReloadCounter] = useState(0);

  useEffect(() => {
    async function loadMe() {
      const token = getToken();
      if (!token) {
        navigate("/login", { replace: true });
        return;
      }

      try {
        const me = (await apiFetch("/auth/me")) as MeResponse;
        setEmail(me.email);
      } catch {
        localStorage.removeItem("token");
        navigate("/login", { replace: true });
      } finally {
        setLoading(false);
      }
    }

    void loadMe();
  }, [navigate]);

  if (loading) {
    return <main style={{ margin: "60px auto", maxWidth: 640 }}>Loading...</main>;
  }

  return (
    <main style={{ margin: "60px auto", maxWidth: 640, fontFamily: "sans-serif" }}>
      <h1>Dashboard</h1>
      <p>Logged in as: {email}</p>
      <StatsPanel reloadSignal={reloadCounter} />
      <LogSessionForm onCreated={() => setReloadCounter((value) => value + 1)} />
      <SessionsList reloadSignal={reloadCounter} />
    </main>
  );
}
