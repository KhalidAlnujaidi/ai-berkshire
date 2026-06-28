import type { Dict } from "@/i18n/ar";

interface VisionProps {
  dict: Dict;
}

export default function Vision({ dict }: VisionProps) {
  const PILLAR_ICONS: Record<string, string> = {
    heart: "M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z",
    chart: "M3 12h4l3-8 4 16 3-8h4",
    flag: "M4 14l8-8m0 0h6m-6 0v12",
  };

  return (
    <section id="vision" className="relative overflow-hidden py-20 md:py-28 bg-mizan-ink">
      {/* Decorative pattern */}
      <div className="absolute inset-0 -z-0 opacity-5" style={{
        backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 0l30 30-30 30L0 30z' fill='%23C5A059'/%3E%3C/svg%3E\")",
      }} />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-block px-4 py-1.5 rounded-full bg-mizan-gold/20 text-mizan-gold text-sm font-medium mb-6 font-arabic">
            {dict.vision.badge}
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4 font-arabic">
            {dict.vision.title}
          </h2>
          <p className="text-lg text-gray-300 max-w-3xl mx-auto font-arabic leading-relaxed">
            {dict.vision.subtitle}
          </p>
        </div>

        {/* Three pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {dict.vision.pillars.map((pillar, i) => (
            <div
              key={i}
              className="p-8 rounded-2xl bg-white/5 border border-white/10 hover:border-mizan-gold/30 hover:bg-white/10 transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-mizan-gold/20 flex items-center justify-center mb-5">
                <svg className="w-6 h-6 text-mizan-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={PILLAR_ICONS[pillar.icon]} />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-white mb-2 font-arabic">{pillar.title}</h3>
              <p className="text-sm text-gray-400 font-arabic">{pillar.description}</p>
            </div>
          ))}
        </div>

        {/* PIF section */}
        <div className="max-w-3xl mx-auto text-center p-8 md:p-12 rounded-2xl bg-gradient-to-r from-mizan-green-dark/40 to-mizan-gold/10 border border-mizan-gold/20">
          <h3 className="text-2xl font-bold text-white mb-3 font-arabic">{dict.vision.pifTitle}</h3>
          <p className="text-gray-300 font-arabic leading-relaxed">{dict.vision.pifDescription}</p>
          <div className="mt-6 text-5xl font-bold text-mizan-gold font-arabic">$925B+</div>
        </div>
      </div>
    </section>
  );
}
