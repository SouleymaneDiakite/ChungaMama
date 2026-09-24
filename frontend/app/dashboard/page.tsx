"use client";

import { useEffect, useState } from "react";
import { useLanguage, ui, pick } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

type Escalation = {
  id: string;
  intent: string | null;
  risk_level: string;
  summary: string;
  reviewed: boolean;
  created_at: string;
};

export default function DashboardPage() {
  const { lang } = useLanguage();
  const t = ui.dashboard;

  const [escalations, setEscalations] = useState<Escalation[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("chungamama_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    fetchEscalations(token);
  }, []);

  async function fetchEscalations(token: string) {
    try {
      const res = await fetch(`${API_BASE}/escalations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 403) {
        setError(true);
        return;
      }
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      setEscalations(await res.json());
    } catch (e: any) {
      setError(true);
    }
  }

  async function markReviewed(id: string) {
    const token = localStorage.getItem("chungamama_token");
    await fetch(`${API_BASE}/escalations/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ reviewed: true }),
    });
    if (token) fetchEscalations(token);
  }

  return (
    <main className="py-14">
      <h1 className="font-display text-3xl text-blue-deep">{pick(t.title, lang)}</h1>
      <p className="text-ink-soft mt-2 mb-8">{pick(t.lede, lang)}</p>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-lg px-4 py-3">
          {pick(t.noAccessError, lang)}
        </div>
      )}

      {!error && escalations === null && <p className="text-ink-soft text-sm">{pick(t.loading, lang)}</p>}

      {!error && escalations?.length === 0 && (
        <p className="text-ink-soft text-sm">{pick(t.empty, lang)}</p>
      )}

      <div className="flex flex-col gap-3">
        {escalations?.map((e) => (
          <div
            key={e.id}
            className={`border rounded-xl p-5 ${
              e.reviewed ? "border-line bg-white" : "border-red-200 bg-red-50"
            }`}
          >
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2.5">
                <span
                  className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    e.risk_level === "high"
                      ? "bg-blue-black text-white"
                      : "bg-blue-pale text-blue-deep"
                  }`}
                >
                  {e.risk_level.toUpperCase()}
                </span>
                <span className="text-sm font-semibold text-ink">{e.intent}</span>
              </div>
              <span className="text-xs text-ink-soft">
                {new Date(e.created_at).toLocaleString()}
              </span>
            </div>
            <pre className="text-sm text-ink-soft mt-3 whitespace-pre-wrap font-body">
              {e.summary}
            </pre>
            {!e.reviewed && (
              <button
                onClick={() => markReviewed(e.id)}
                className="mt-3 text-xs font-semibold bg-blue-deep text-white px-3.5 py-1.5 rounded-lg"
              >
                {pick(t.markReviewed, lang)}
              </button>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
