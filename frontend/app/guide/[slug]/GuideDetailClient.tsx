"use client";

import Link from "next/link";
import { notFound } from "next/navigation";
import { getTopicBySlug } from "@/lib/guideContent";
import { GuideIcon } from "@/lib/GuideIcon";
import { useLanguage, ui, pick } from "@/lib/i18n";

export function GuideDetailClient({ slug }: { slug: string }) {
  const { lang } = useLanguage();
  const topic = getTopicBySlug(slug);
  if (!topic) return notFound();

  const accentBg =
    topic.accent === "maroon" ? "bg-red-50 border-red-200 text-red-800" :
    topic.accent === "gold" ? "bg-[#FBF3E4] border-[#E8D7B0] text-[#6B4E1E]" :
    "bg-blue-pale border-blue-mid/30 text-blue-deep";

  return (
    <main className="py-14 max-w-2xl">
      <Link href="/guide" className="text-sm text-blue-mid font-semibold">
        &larr; {pick(ui.guideDetail.back, lang)}
      </Link>

      <div className="flex items-center gap-3 mt-4">
        <div className="w-12 h-12 rounded-lg bg-blue-pale flex items-center justify-center shrink-0">
          <GuideIcon name={topic.icon} className="text-blue-deep" />
        </div>
        <h1 className="font-display text-3xl text-blue-deep">{pick(topic.title, lang)}</h1>
      </div>
      <p className="text-ink-soft mt-3">{pick(topic.shortDesc, lang)}</p>

      <div className="rounded-2xl overflow-hidden bg-blue-pale aspect-[16/9] relative mt-6">
        <img
          src={topic.image}
          alt={pick(topic.title, lang)}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      </div>

      {topic.slug === "dalili-za-hatari" && (
        <div className={`mt-6 border rounded-xl px-4 py-3 text-sm font-medium ${accentBg}`}>
          {pick(ui.guideDetail.dangerBanner, lang)}
        </div>
      )}

      <div className="flex flex-col gap-8 mt-10">
        {topic.sections.map((section, si) => (
          <div key={si}>
            <h2 className="font-display text-xl text-blue-deep mb-3">{pick(section.heading, lang)}</h2>
            <ul className="flex flex-col gap-2">
              {section.body.map((line, i) => (
                <li key={i} className="text-sm text-ink-soft leading-relaxed flex gap-2.5">
                  <span className="text-gold mt-1.5 shrink-0">&#8226;</span>
                  <span>{pick(line, lang)}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-12 border-t border-line pt-8 flex items-center justify-between flex-wrap gap-4">
        <p className="text-sm text-ink-soft">{pick(ui.guideDetail.questionPrompt, lang)}</p>
        <Link
          href="/assistant"
          className="bg-blue-deep text-white px-5 py-2.5 rounded-lg text-sm font-semibold"
        >
          {pick(ui.guideDetail.askAssistant, lang)}
        </Link>
      </div>
    </main>
  );
}
