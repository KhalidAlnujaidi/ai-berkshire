"use client";

import { getDict, type Locale } from "@/i18n";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ZakatCalculator from "@/components/ZakatCalculator";

export default function ZakatPage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="pt-16 md:pt-20">
        <ZakatCalculator dict={dict} locale={locale} />
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
