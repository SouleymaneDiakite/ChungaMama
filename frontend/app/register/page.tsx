"use client";

import { useState } from "react";
import { useLanguage, ui, pick } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function RegisterPage() {
  const { lang } = useLanguage();
  const t = ui.register;

  const [fullName, setFullName] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("mother");
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    const isEmail = identifier.includes("@");
    const payload = isEmail
      ? { full_name: fullName || null, email: identifier, password, role }
      : { full_name: fullName || null, phone: identifier, password, role };

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
      setStatus("done");
      setMessage(pick(t.successMessage, lang));
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
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder={pick(t.namePlaceholder, lang)}
          className="border border-line rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-mid"
        />
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
        <div>
          <label className="text-xs text-ink-soft mb-1 block">{pick(t.roleLabel, lang)}</label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full border border-line rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-mid bg-white"
          >
            <option value="mother">{pick(t.roleMother, lang)}</option>
            <option value="chw">{pick(t.roleChw, lang)}</option>
            <option value="clinician">{pick(t.roleClinician, lang)}</option>
            <option value="admin">{pick(t.roleAdmin, lang)}</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={status === "loading"}
          className="bg-blue-deep text-white rounded-lg py-2.5 text-sm font-semibold mt-1 disabled:opacity-50"
        >
          {status === "loading" ? pick(t.submitting, lang) : pick(t.submit, lang)}
        </button>
      </form>
      {message && (
        <p className={`text-sm mt-4 ${status === "error" ? "text-red-700" : "text-green-700"}`}>
          {message}
        </p>
      )}
      <p className="text-xs text-ink-soft mt-4">
        {pick(t.haveAccount, lang)}{" "}
        <a href="/login" className="text-blue-mid font-semibold">
          {pick(t.loginLink, lang)}
        </a>
      </p>
    </main>
  );
}
