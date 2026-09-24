"use client";

export function HeroTopImage() {
  return (
    <div className="rounded-2xl overflow-hidden bg-blue-pale aspect-[4/3] relative">
      <img
        src="/images/hero-top.jpg"
        alt="ChungaMama"
        className="w-full h-full object-cover"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = "none";
        }}
      />
    </div>
  );
}
