"use client";

import Link from "next/link";
import { guideTopics } from "@/lib/guideContent";
import { GuideIcon } from "@/lib/GuideIcon";
import { useLanguage, ui, pick } from "@/lib/i18n";

export default function GuidePage() {
  const { lang } = useLanguage();

  return (
    <main className="py-16">
      <h1 className="font-display text-3xl text-blue-deep">{pick(ui.guideIndex.title, lang)}</h1>
      <p className="mt-3 text-ink-soft max-w-lg">{pick(ui.guideIndex.lede, lang)}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-10">
        {guideTopics.map((topic) => (
          <Link
            key={topic.slug}
            href={`/guide/${topic.slug}`}
            className="flex items-start gap-4 border border-line rounded-2xl p-6 bg-white hover:border-blue-mid hover:shadow-md transition-all"
          >
            <div className="w-11 h-11 rounded-lg bg-blue-pale flex items-center justify-center shrink-0">
              <GuideIcon name={topic.icon} className="text-blue-deep" />
            </div>
            <div>
              <h2 className="font-display text-lg text-blue-deep">{pick(topic.title, lang)}</h2>
              <p className="text-sm text-ink-soft mt-1.5 leading-relaxed">{pick(topic.shortDesc, lang)}</p>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
