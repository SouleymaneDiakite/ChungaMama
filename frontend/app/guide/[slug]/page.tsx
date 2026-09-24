import { guideTopics } from "@/lib/guideContent";
import { GuideDetailClient } from "./GuideDetailClient";

export function generateStaticParams() {
  return guideTopics.map((topic) => ({ slug: topic.slug }));
}

export default function GuideDetailPage({ params }: { params: { slug: string } }) {
  return <GuideDetailClient slug={params.slug} />;
}
