"use client";

import { useState } from "react";
import { useLanguage, ui, pick } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function LoginPage() {
  const { lang } = useLanguage();
  const t = ui.login;

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    const isEmail = identifier.includes("@");
    const payload = isEmail
      ? { email: identifier, password }
      : { phone: identifier, password };

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);

      localStorage.setItem("chungamama_token", data.access_token);
      window.location.href = "/";
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message);
    }
  }

  return (
    <main className="py-16 max-w-sm mx-auto">
      <h1 className="font-display text-2xl text-blue-deep mb-6">{pick(t.title, lang)}</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          placeholder={pick(t.identifierPlaceholder, lang)}
          className="border border-line rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-mid"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={pick(t.passwordPlaceholder, lang)}
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
      <a href="/forgot-password" className="text-xs text-blue-mid font-semibold mt-3 inline-block">
        {pick(t.forgotPassword, lang)}
      </a>
      {message && <p className="text-sm mt-4 text-red-700">{message}</p>}
      <p className="text-xs text-ink-soft mt-4">
        {pick(t.noAccount, lang)}{" "}
        <a href="/register" className="text-blue-mid font-semibold">
          {pick(t.registerLink, lang)}
        </a>
      </p>
    </main>
  );
}
