import type { Dict } from "@/i18n/ar";

interface HowItWorksProps {
  dict: Dict;
}

export default function HowItWorks({ dict }: HowItWorksProps) {
  return (
    <section id="how-it-works" className="py-20 md:py-28 bg-mizan-cream">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-4 font-arabic">
            {dict.howItWorks.title}
          </h2>
          <p className="text-lg text-mizan-slate font-arabic">{dict.howItWorks.subtitle}</p>
        </div>

        <div className="relative">
          {/* Connecting line */}
          <div className="hidden md:block absolute top-24 right-0 left-0 h-0.5 bg-gradient-to-r from-mizan-green/0 via-mizan-green/30 to-mizan-green/0" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-4">
            {dict.howItWorks.steps.map((step, i) => (
              <div key={i} className="relative text-center">
                {/* Number circle */}
                <div className="relative z-10 w-20 h-20 mx-auto mb-6 rounded-full bg-white border-4 border-mizan-green/20 flex items-center justify-center shadow-md">
                  <span className="text-3xl font-bold text-mizan-green font-arabic">{step.number}</span>
                </div>

                <h3 className="text-xl font-bold text-mizan-ink mb-2 font-arabic">{step.title}</h3>
                <p className="text-sm text-mizan-slate font-arabic leading-relaxed max-w-xs mx-auto">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-16">
          <a
            href="#checker"
            className="inline-flex items-center gap-2 px-8 py-4 text-base font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 font-arabic"
          >
            {dict.hero.ctaPrimary}
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}
