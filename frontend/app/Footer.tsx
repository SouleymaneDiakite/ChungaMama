"use client";

import { useLanguage, ui, pick } from "@/lib/i18n";

export function Footer() {
  const { lang } = useLanguage();
  return (
    <footer className="bg-blue-black mt-16">
      <div className="max-w-6xl mx-auto px-7 py-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <span className="font-display font-semibold text-white notranslate">ChungaMama</span>
          <p className="text-xs text-white/60 mt-1 max-w-xs">{pick(ui.footer.tagline, lang)}</p>
        </div>
        <div className="flex items-center gap-6 text-sm">
          <a href="/guide" className="text-white/75 hover:text-white">{pick(ui.nav.guide, lang)}</a>
          <a href="/assistant" className="text-white/75 hover:text-white">{pick(ui.nav.assistant, lang)}</a>
          <a href="/login" className="text-white/75 hover:text-white">{pick(ui.nav.login, lang)}</a>
        </div>
        <p className="text-xs text-white/50">{pick(ui.footer.copyright, lang)}</p>
      </div>
    </footer>
  );
}
