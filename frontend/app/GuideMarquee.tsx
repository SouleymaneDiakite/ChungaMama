"use client";

import Link from "next/link";
import { guideTopics } from "@/lib/guideContent";
import { GuideIcon } from "@/lib/GuideIcon";
import { useLanguage, pick } from "@/lib/i18n";

export function GuideMarquee() {
  const { lang } = useLanguage();
  const cards = [...guideTopics, ...guideTopics]; // duplicated for a seamless loop

  return (
    <div className="bg-blue-pale border-y border-line -mx-7 px-7 py-8 overflow-hidden my-2">
      <div className="marquee-track flex gap-4 w-max">
        {cards.map((topic, i) => {
          const title = pick(topic.title, lang);
          const desc = pick(topic.shortDesc, lang);
          return (
            <Link
              key={`${topic.slug}-${i}`}
              href={`/guide/${topic.slug}`}
              className="flex items-center gap-3.5 bg-white border border-line rounded-2xl px-6 py-4 whitespace-nowrap shadow-sm hover:border-blue-mid hover:shadow-md transition-all"
            >
              <div className="w-9 h-9 rounded-lg bg-blue-pale flex items-center justify-center shrink-0">
                <GuideIcon name={topic.icon} className="text-blue-deep" />
              </div>
              <div>
                <span className="text-base font-semibold text-blue-deep block">{title}</span>
                <span className="text-xs text-ink-soft">
                  {desc.length > 32 ? desc.slice(0, 32) + "..." : desc}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
