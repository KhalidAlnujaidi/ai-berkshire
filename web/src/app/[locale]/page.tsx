"use client";

import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import TrackRecord from "@/components/TrackRecord";
import Hero from "@/components/Hero";
import TrustBar from "@/components/TrustBar";
import HalalStocksGrid from "@/components/HalalStocksGrid";
import ShariaChecker from "@/components/ShariaChecker";
import StockCompare from "@/components/StockCompare";
import Features from "@/components/Features";
import PortfolioScreener from "@/components/PortfolioScreener";
import HowItWorks from "@/components/HowItWorks";
import Vision2030 from "@/components/Vision2030";
import Pricing from "@/components/Pricing";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";

export default function HomePage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);

  useLocaleAttrs(locale, dir);

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main>
        <Hero dict={dict} />
        <TrustBar locale={locale} />
        <TrackRecord dict={dict} />
        <HalalStocksGrid dict={dict} locale={locale} />
        <PortfolioScreener dict={dict} locale={locale} />
        <ShariaChecker dict={dict} locale={locale} />
        <StockCompare dict={dict} locale={locale} />
        <Features dict={dict} />
        <HowItWorks dict={dict} />
        <Vision2030 dict={dict} />
        <Pricing dict={dict} />
        <CTASection dict={dict} />
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
