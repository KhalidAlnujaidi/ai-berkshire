"use client";

import { useEffect } from "react";

/**
 * Sets document.documentElement.lang and .dir based on the locale.
 * Must be rendered inside a client component tree.
 */
export function useLocaleAttrs(locale: string, dir: "rtl" | "ltr") {
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dir;
  }, [locale, dir]);
}
