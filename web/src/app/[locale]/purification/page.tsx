"use client";

import { getDict, type Locale } from "@/i18n";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import PurificationCalculator from "@/components/PurificationCalculator";

export default function PurificationPage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="pt-16 md:pt-20">
        <PurificationCalculator dict={dict} locale={locale} />
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
