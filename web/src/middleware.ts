import { defaultLocale } from "@/i18n";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const locales = ["ar", "en"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if the pathname has a locale
  const pathnameIsMissingLocale = locales.every(
    (locale) => !pathname.startsWith(`/${locale}/`) && pathname !== `/${locale}`
  );

  // Redirect if there is no locale
  if (pathnameIsMissingLocale) {
    const locale = defaultLocale; // 'ar' — Arabic is default
    return NextResponse.redirect(
      new URL(`/${locale}${pathname.startsWith("/") ? "" : "/"}${pathname}`, request.url)
    );
  }
}

export const config = {
  matcher: [
    // Skip all internal paths (_next, api, assets)
    "/((?!_next|api|.*\\..*).*)",
  ],
};
