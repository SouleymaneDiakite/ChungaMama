"use client";

import { useEffect, useState } from "react";
import { useLanguage, ui, pick } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

type CurrentUser = {
  full_name: string | null;
  email: string | null;
  phone: string | null;
};

export function NavBar() {
  const { lang, setLang } = useLanguage();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("chungamama_token");
    if (!token) {
      setChecked(true);
      return;
    }
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setUser(data);
        else localStorage.removeItem("chungamama_token"); // stale/expired token
      })
      .finally(() => setChecked(true));
  }, []);

  function logout() {
    localStorage.removeItem("chungamama_token");
    window.location.href = "/";
  }

  const displayName = user?.full_name || user?.email || user?.phone;

  return (
    <nav className="bg-blue-black" translate="no">
      <div className="max-w-6xl mx-auto px-7 flex items-center justify-between py-5">
        <a href="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-mid flex items-center justify-center">
            <span className="text-white font-display text-sm">C</span>
          </div>
          <span className="font-display font-semibold text-lg text-white notranslate">ChungaMama</span>
        </a>
        <div className="flex items-center gap-5 md:gap-8 text-sm font-medium">
          <a href="/guide" className="hidden md:inline text-white/75 hover:text-white">
            {pick(ui.nav.guide, lang)}
          </a>
          <a href="/assistant" className="hidden md:inline text-white/75 hover:text-white">
            {pick(ui.nav.assistant, lang)}
          </a>

          <div className="flex items-center border border-white/25 rounded-full overflow-hidden text-xs font-semibold">
            <button
              onClick={() => setLang("sw")}
              className={`px-3 py-1.5 ${lang === "sw" ? "bg-white text-blue-black" : "text-white/70"}`}
            >
              SW
            </button>
            <button
              onClick={() => setLang("en")}
              className={`px-3 py-1.5 ${lang === "en" ? "bg-white text-blue-black" : "text-white/70"}`}
            >
              EN
            </button>
          </div>

          {!checked ? null : user ? (
            <div className="hidden md:flex items-center gap-3.5">
              <span className="text-white/90">
                {pick(ui.nav.greeting, lang)} {displayName}
              </span>
              <button
                onClick={logout}
                className="text-white/60 hover:text-white text-xs border border-white/25 rounded-lg px-3 py-1.5"
              >
                {pick(ui.nav.logout, lang)}
              </button>
            </div>
          ) : (
            <a
              href="/login"
              className="bg-blue-mid text-white px-5 py-2 rounded-lg font-semibold hover:bg-[#3689B0]"
            >
              {pick(ui.nav.login, lang)}
            </a>
          )}
        </div>
      </div>
    </nav>
  );
}
