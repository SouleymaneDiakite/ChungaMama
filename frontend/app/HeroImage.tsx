"use client";

export function HeroImage() {
  return (
    <div className="rounded-2xl overflow-hidden bg-blue-pale aspect-[4/3] relative">
      <img
        src="/hero-photo.jpg"
        alt="Mama mjamzito"
        className="w-full h-full object-cover"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = "none";
        }}
      />
    </div>
  );
}
