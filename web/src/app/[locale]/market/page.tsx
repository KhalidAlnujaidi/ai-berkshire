"use client";

import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import MarketDashboard from "@/components/MarketDashboard";

export default function MarketPage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);

  useLocaleAttrs(locale, dir);

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="pt-16 md:pt-20">
        <MarketDashboard dict={dict} locale={locale} />
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
