"use client";

import { getDict, type Locale } from "@/i18n";
import AuthPage from "@/components/AuthPage";

export default function LoginPage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);

  return <AuthPage dict={dict} locale={locale} mode="login" />;
}
