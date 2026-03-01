import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch, getToken } from "../api/client";
import LogSessionForm from "../components/LogSessionForm";
import MyCollection from "../components/MyCollection";
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
    return <main className="page-shell">Loading...</main>;
  }

  return (
    <main className="page-shell">
      <h1 className="dashboard-title">Game Night Dashboard</h1>
      <p className="dashboard-user">Logged in as: {email}</p>
      <StatsPanel reloadSignal={reloadCounter} />
      <MyCollection
        reloadSignal={reloadCounter}
        onCollectionChanged={() => setReloadCounter((value) => value + 1)}
      />
      <section className="split">
        <LogSessionForm
          reloadSignal={reloadCounter}
          onCreated={() => setReloadCounter((value) => value + 1)}
          onCollectionChanged={() => setReloadCounter((value) => value + 1)}
        />
        <SessionsList reloadSignal={reloadCounter} />
      </section>
    </main>
  );
}
