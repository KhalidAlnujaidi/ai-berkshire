"use client";

import Link from "next/link";
import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function NotFound({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);
  useLocaleAttrs(locale, dir);

  const t = dict.notFound;

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="min-h-[70vh] flex items-center justify-center pt-24 pb-20">
        <div className="max-w-md mx-auto px-4 text-center">
          {/* Big 404 */}
          <div className="relative mb-8">
            <div className="text-9xl font-bold text-mizan-green/10 select-none">404</div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-mizan-green to-mizan-green-dark flex items-center justify-center shadow-lg">
                <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12 text-white">
                  <path d="M12 3v18M5 8h14M7 8l-2 6a4 4 0 008 0L11 8M13 8l-2 6a4 4 0 008 0L17 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            </div>
          </div>

          <h1 className={`text-3xl font-bold text-mizan-ink mb-3 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.title}
          </h1>
          <p className={`text-mizan-slate mb-8 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
            {t.message}
          </p>

          {/* Quick links */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
            <p className={`text-sm text-mizan-slate mb-4 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
              {t.suggestTitle}
            </p>
            <div className="flex flex-col gap-2">
              <Link href={`/${locale}#checker`} className="px-4 py-2 text-sm text-mizan-green hover:bg-mizan-green-pale rounded-lg transition-colors font-medium">
                {t.links.sharia}
              </Link>
              <Link href={`/${locale}#discover`} className="px-4 py-2 text-sm text-mizan-green hover:bg-mizan-green-pale rounded-lg transition-colors font-medium">
                {t.links.stocks}
              </Link>
              <Link href={`/${locale}/learn`} className="px-4 py-2 text-sm text-mizan-green hover:bg-mizan-green-pale rounded-lg transition-colors font-medium">
                {t.links.learn}
              </Link>
            </div>
          </div>

          <Link
            href={`/${locale}`}
            className="inline-block px-8 py-3 bg-mizan-green hover:bg-mizan-green-dark text-white font-semibold rounded-lg transition-colors shadow-sm"
          >
            {t.cta}
          </Link>
        </div>
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
