"use client";

import type { Dict } from "@/i18n/ar";

interface HeroProps {
  dict: Dict;
}

export default function Hero({ dict }: HeroProps) {
  return (
    <section className="relative overflow-hidden pt-32 pb-20 md:pt-40 md:pb-28">
      {/* Background gradient orbs */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-mizan-green/8 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-mizan-gold/8 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-mizan-green-pale border border-mizan-green/20 text-mizan-green text-sm font-medium mb-8 animate-fade-in-up">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-mizan-green opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-mizan-green"></span>
            </span>
            {dict.hero.badge}
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl font-bold text-mizan-ink leading-tight mb-6 animate-fade-in-up font-arabic">
            {dict.hero.title}
            <br />
            <span className="bg-gradient-to-r from-mizan-green to-mizan-gold bg-clip-text text-transparent">
              {dict.hero.titleHighlight}
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-mizan-slate leading-relaxed max-w-2xl mx-auto mb-10 animate-fade-in-up font-arabic">
            {dict.hero.subtitle}
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up">
            <a
              href="#checker"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 font-arabic"
            >
              {dict.hero.ctaPrimary}
            </a>
            <a
              href="#how-it-works"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-mizan-green bg-white hover:bg-mizan-green-pale border-2 border-mizan-green/20 rounded-xl transition-all font-arabic"
            >
              {dict.hero.ctaSecondary}
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 animate-fade-in-up">
            {[
              { value: dict.hero.statValues.investors, label: dict.hero.stats.investors },
              { value: dict.hero.statValues.stocks, label: dict.hero.stats.stocks },
              { value: dict.hero.statValues.sharia, label: dict.hero.stats.sharia },
              { value: dict.hero.statValues.accuracy, label: dict.hero.stats.accuracy },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-mizan-green font-arabic">
                  {stat.value}
                </div>
                <div className="text-sm text-mizan-slate mt-1 font-arabic">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
