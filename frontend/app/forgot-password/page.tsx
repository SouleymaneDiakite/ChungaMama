"use client";

import { useState } from "react";
import { useLanguage, ui, pick } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function ForgotPasswordPage() {
  const { lang } = useLanguage();
  const t = ui.forgotPassword;

  const [identifier, setIdentifier] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "done">("idle");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");

    const isEmail = identifier.includes("@");
    const payload = isEmail ? { email: identifier } : { phone: identifier };

    try {
      await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } finally {
      // Always show the same generic confirmation, whether or not the
      // request succeeded at the network level — matches the backend's
      // intentional "don't reveal if this account exists" behavior.
      setStatus("done");
    }
  }

  return (
    <main className="py-16 max-w-sm mx-auto">
      <h1 className="font-display text-2xl text-blue-deep mb-3">{pick(t.title, lang)}</h1>

      {status === "done" ? (
        <p className="text-sm text-green-700 mt-4">{pick(t.genericSuccess, lang)}</p>
      ) : (
        <>
          <p className="text-sm text-ink-soft mb-6">{pick(t.lede, lang)}</p>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <input
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder={pick(ui.login.identifierPlaceholder, lang)}
              className="border border-line rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-mid"
            />
            <button
              type="submit"
              disabled={status === "loading"}
              className="bg-blue-deep text-white rounded-lg py-2.5 text-sm font-semibold mt-1 disabled:opacity-50"
            >
              {status === "loading" ? pick(t.submitting, lang) : pick(t.submit, lang)}
            </button>
          </form>
        </>
      )}

      <p className="text-xs text-ink-soft mt-6">
        <a href="/login" className="text-blue-mid font-semibold">
          &larr; {pick(t.backToLogin, lang)}
        </a>
      </p>
    </main>
  );
}
