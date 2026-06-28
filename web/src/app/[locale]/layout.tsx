import { notFound } from "next/navigation";
import { getDict, getDirection, type Locale } from "@/i18n";
import type { Metadata } from "next";

const locales: Locale[] = ["ar", "en"];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const dict = getDict(params.locale);
  return {
    title: dict.meta.title,
    description: dict.meta.description,
    openGraph: {
      title: dict.meta.title,
      description: dict.meta.description,
      locale: params.locale === "ar" ? "ar_SA" : "en_US",
      type: "website",
    },
  };
}

export default function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!locales.includes(params.locale as Locale)) {
    notFound();
  }

  const dir = getDirection(params.locale);

  // We need to set lang and dir on the html element.
  // Since the root layout renders <html>, we use a client component
  // to update document attributes after hydration.
  return (
    <div data-locale={params.locale} data-dir={dir}>
      {children}
    </div>
  );
}
