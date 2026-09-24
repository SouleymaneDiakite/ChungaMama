"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useLanguage, ui, pick } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

function ResetPasswordForm() {
  const { lang } = useLanguage();
  const t = ui.resetPassword;
  const token = useSearchParams().get("token");

  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) {
      setStatus("error");
      setMessage(pick(t.missingToken, lang));
      return;
    }
    setStatus("loading");

    try {
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (!res.ok) throw new Error(pick(t.invalidLink, lang));
      setStatus("done");
      setMessage(pick(t.success, lang));
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message);
    }
  }

  return (
    <main className="py-16 max-w-sm mx-auto">
      <h1 className="font-display text-2xl text-blue-deep mb-6">{pick(t.title, lang)}</h1>

      {status === "done" ? (
        <>
          <p className="text-sm text-green-700">{message}</p>
          <a href="/login" className="text-sm text-blue-mid font-semibold mt-4 inline-block">
            {pick(ui.login.submit, lang)} &rarr;
          </a>
        </>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={pick(t.newPasswordPlaceholder, lang)}
            className="border border-line rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-mid"
          />
          <button
            type="submit"
            disabled={status === "loading"}
            className="bg-blue-deep text-white rounded-lg py-2.5 text-sm font-semibold mt-1 disabled:opacity-50"
          >
            {status === "loading" ? pick(t.submitting, lang) : pick(t.submit, lang)}
          </button>
          {status === "error" && <p className="text-sm text-red-700 mt-1">{message}</p>}
        </form>
      )}
    </main>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
