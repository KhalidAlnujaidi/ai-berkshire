import { ar } from "./ar";
import { en } from "./en";
import type { Dict } from "./ar";

export type Locale = "ar" | "en";

export const dictionaries: Record<Locale, Dict> = { ar, en };

export function getDict(locale: string): Dict {
  return dictionaries[locale as Locale] ?? ar; // default to Arabic
}

export function getDirection(locale: string): "rtl" | "ltr" {
  return locale === "en" ? "ltr" : "rtl";
}

export function getLocaleLabel(locale: string): string {
  return locale === "en" ? "English" : "العربية";
}

export const defaultLocale: Locale = "ar";
