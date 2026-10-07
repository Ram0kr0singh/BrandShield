import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { getHealth, type Health } from "./api";
import "./styles.css";

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setError("API unavailable"));
  }, []);

  const status = error ?? (health ? `API ${health.status}; database ${health.database}` : "Checking API…");
  return (
    <main>
      <section className="card">
        <ShieldCheck aria-hidden="true" size={42} />
        <p className="eyebrow">Digital Risk Protection</p>
        <h1>BrandShield</h1>
        <p className="description">Development foundation is ready for future monitoring and detection work.</p>
        <p className={error || health?.status === "degraded" ? "status warning" : "status"}>{status}</p>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<BrowserRouter><App /></BrowserRouter>);
