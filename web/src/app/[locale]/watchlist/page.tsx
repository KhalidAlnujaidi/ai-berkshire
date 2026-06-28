"use client";

import { getDict, getDirection, type Locale } from "@/i18n";
import WatchlistPage from "@/components/WatchlistPage";

export default function WatchlistRoute({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  getDirection(locale);

  return <WatchlistPage dict={dict} locale={locale} />;
}
