"use client";

import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function PrivacyPage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);
  useLocaleAttrs(locale, dir);

  const t = dict.legalPages.privacy;

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="pt-24 pb-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-12 text-center">
            <h1 className={`text-4xl font-bold text-mizan-ink mb-4 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
              {t.title}
            </h1>
            <p className="text-sm text-mizan-slate">{t.lastUpdated}</p>
          </div>

          <p className={`text-mizan-slate mb-8 leading-relaxed ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.intro}
          </p>

          <div className="space-y-8">
            {t.sections.map((section, i) => (
              <section key={i}>
                <h2 className={`text-xl font-semibold text-mizan-ink mb-3 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                  {section.heading}
                </h2>
                <p className={`text-mizan-slate leading-relaxed ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                  {section.body}
                </p>
              </section>
            ))}
          </div>
        </div>
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
