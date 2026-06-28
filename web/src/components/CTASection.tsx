import type { Dict } from "@/i18n/ar";

interface CTASectionProps {
  dict: Dict;
}

export default function CTASection({ dict }: CTASectionProps) {
  return (
    <section className="py-20 md:py-28">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-mizan-green via-mizan-green-dark to-mizan-ink p-12 md:p-20 text-center">
          {/* Decorative orbs */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-mizan-gold/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/5 rounded-full blur-3xl" />

          <div className="relative z-10">
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-4 font-arabic">
              {dict.cta.title}
            </h2>
            <p className="text-lg text-gray-200 mb-8 font-arabic">{dict.cta.subtitle}</p>

            <a
              href="#checker"
              className="inline-flex items-center gap-2 px-10 py-4 text-base font-bold text-mizan-ink bg-white hover:bg-mizan-gold rounded-xl transition-all shadow-xl hover:-translate-y-0.5 font-arabic"
            >
              {dict.cta.button}
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </a>

            <p className="text-sm text-gray-300 mt-4 font-arabic">{dict.cta.note}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
