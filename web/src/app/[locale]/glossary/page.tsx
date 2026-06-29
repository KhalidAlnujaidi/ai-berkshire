"use client";

import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import GlossaryPage from "@/components/GlossaryPage";
import Footer from "@/components/Footer";

export default function GlossaryRoute({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);

  useLocaleAttrs(locale, dir);

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main>
        <GlossaryPage dict={dict} locale={locale} />
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
