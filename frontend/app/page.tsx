"use client";

import Link from "next/link";
import { guideTopics } from "@/lib/guideContent";
import { GuideIcon } from "@/lib/GuideIcon";
import { GuideMarquee } from "./GuideMarquee";
import { HeroImage } from "./HeroImage";
import { HeroTopImage } from "./HeroTopImage";
import { useLanguage, ui, pick } from "@/lib/i18n";

export default function Home() {
  const { lang } = useLanguage();
  const t = ui.home;

  return (
    <main>
      <section className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center pt-14 pb-10 md:pt-16">
        <div>
          <h1 className="font-display text-4xl md:text-5xl text-blue-deep leading-tight">
            {pick(t.heroTitle, lang)}
          </h1>
          <p className="mt-5 text-ink-soft leading-relaxed">{pick(t.heroLede, lang)}</p>
        </div>
        <HeroTopImage />
      </section>

      <GuideMarquee />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center py-10">
        <div>
          <div className="flex gap-3.5 flex-wrap">
            <Link
              href="/assistant"
              className="flex items-center gap-2.5 bg-blue-deep text-white px-6 py-3.5 rounded-lg font-semibold"
            >
              <GuideIcon name="mic" />
              {pick(t.ctaVoice, lang)}
            </Link>
            <Link
              href="/assistant"
              className="flex items-center gap-2.5 bg-white text-blue-deep border-2 border-blue-deep px-6 py-3.5 rounded-lg font-semibold"
            >
              <GuideIcon name="chat" />
              {pick(t.ctaText, lang)}
            </Link>
          </div>
          <div className="mt-5 text-sm text-ink-soft flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-gold inline-block" />
            {pick(t.trustLine, lang)}
          </div>
        </div>

        <HeroImage />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 py-10 border-t border-line">
        <Pillar title={pick(t.pillar1Title, lang)}>{pick(t.pillar1Body, lang)}</Pillar>
        <Pillar title={pick(t.pillar2Title, lang)}>{pick(t.pillar2Body, lang)}</Pillar>
        <Pillar title={pick(t.pillar3Title, lang)}>{pick(t.pillar3Body, lang)}</Pillar>
      </div>

      <section className="py-16 border-t border-line">
        <h2 className="font-display text-3xl text-blue-deep">{pick(t.guideSectionTitle, lang)}</h2>
        <p className="mt-3 text-ink-soft max-w-lg">{pick(t.guideSectionLede, lang)}</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-line border border-line rounded-2xl overflow-hidden mt-10">
          {guideTopics.slice(0, 3).map((topic) => (
            <Link
              key={topic.slug}
              href={`/guide/${topic.slug}`}
              className="bg-paper hover:bg-blue-pale/40 transition-colors p-7"
            >
              <h3 className="font-display text-lg text-blue-deep">{pick(topic.title, lang)}</h3>
              <p className="text-sm text-ink-soft mt-2.5 leading-relaxed">{pick(topic.shortDesc, lang)}</p>
            </Link>
          ))}
        </div>
        <Link
          href="/guide"
          className="inline-block mt-6 text-sm font-semibold text-blue-mid border-b border-blue-mid"
        >
          {pick(t.seeAllTopics, lang)}
        </Link>
      </section>

      <div className="flex justify-between flex-wrap gap-3 pt-9">
        <p className="text-sm text-ink-soft">{pick(t.chwPrompt, lang)}</p>
        <Link href="/dashboard" className="text-sm font-semibold text-blue-mid border-b border-blue-mid">
          {pick(t.dashboardLink, lang)}
        </Link>
      </div>
    </main>
  );
}

function Pillar({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="font-semibold text-ink">{title}</h3>
      <p className="text-sm text-ink-soft mt-1 leading-relaxed">{children}</p>
    </div>
  );
}
