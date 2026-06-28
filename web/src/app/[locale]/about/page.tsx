"use client";

import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function AboutPage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);
  useLocaleAttrs(locale, dir);

  const t = dict.about;

  const valueIcons: Record<string, string> = {
    scale: "⚖️",
    mosque: "🕌",
    shield: "🛡️",
    lightbulb: "💡",
  };

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="pt-24 pb-20">
        {/* Hero */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center mb-16">
          <div className="inline-block mb-6">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-mizan-green to-mizan-green-dark flex items-center justify-center shadow-lg mx-auto">
              <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12 text-white">
                <path d="M12 3v18M5 8h14M7 8l-2 6a4 4 0 008 0L11 8M13 8l-2 6a4 4 0 008 0L17 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          </div>
          <h1 className={`text-4xl md:text-5xl font-bold text-mizan-ink mb-4 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.title}
          </h1>
          <p className={`text-lg text-mizan-slate ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.subtitle}
          </p>
        </div>

        {/* Stats */}
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mb-20">
          <h2 className={`text-center text-2xl font-semibold text-mizan-ink mb-8 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.statsTitle}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {t.stats.map((stat, i) => (
              <div key={i} className="bg-white rounded-xl p-6 text-center shadow-sm border border-gray-100">
                <div className="text-3xl font-bold text-mizan-green mb-1">{stat.value}</div>
                <div className={`text-sm text-mizan-slate ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Story */}
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 mb-20">
          <h2 className={`text-3xl font-bold text-mizan-ink mb-8 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.storyTitle}
          </h2>
          <div className="space-y-6">
            {t.storyText.map((para, i) => (
              <p key={i} className={`text-mizan-slate leading-relaxed text-lg ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                {para}
              </p>
            ))}
          </div>
        </div>

        {/* Mission */}
        <div className="bg-gradient-to-br from-mizan-green to-mizan-green-dark py-16 mb-20">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className={`text-3xl font-bold text-white mb-6 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
              {t.missionTitle}
            </h2>
            <p className={`text-xl text-white/90 leading-relaxed ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
              {t.missionText}
            </p>
          </div>
        </div>

        {/* Values */}
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mb-20">
          <h2 className={`text-center text-3xl font-bold text-mizan-ink mb-12 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.valuesTitle}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {t.values.map((value, i) => (
              <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex gap-4">
                <div className="text-4xl flex-shrink-0">{valueIcons[value.icon] || "⭐"}</div>
                <div>
                  <h3 className={`text-lg font-semibold text-mizan-ink mb-2 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                    {value.title}
                  </h3>
                  <p className={`text-sm text-mizan-slate leading-relaxed ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                    {value.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Team */}
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className={`text-3xl font-bold text-mizan-ink mb-6 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.teamTitle}
          </h2>
          <p className={`text-lg text-mizan-slate leading-relaxed ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.teamText}
          </p>
        </div>
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
