"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import type { Dict } from "@/i18n/ar";

interface NavbarProps {
  dict: Dict;
  locale: string;
}

export default function Navbar({ dict, locale }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const navItems = [
    { href: "#features", label: dict.nav.features },
    { href: "#checker", label: dict.nav.shariaChecker },
    { href: "#pricing", label: dict.nav.pricing },
    { href: "#vision", label: dict.nav.vision2030 },
  ];

  const switchLocale = locale === "ar" ? "en" : "ar";
  const switchHref = `/${switchLocale}`;

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/90 backdrop-blur-md shadow-sm border-b border-mizan-green/10"
          : "bg-transparent"
      }`}
    >
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <Link href={`/${locale}`} className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mizan-green to-mizan-green-dark flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
              <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 text-white">
                <path
                  d="M12 3v18M5 8h14M7 8l-2 6a4 4 0 008 0L11 8M13 8l-2 6a4 4 0 008 0L17 8"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <span className="text-xl font-bold text-mizan-ink font-arabic">
              {locale === "ar" ? "ميزان" : "Mizan"}
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="text-sm font-medium text-mizan-slate hover:text-mizan-green transition-colors font-arabic"
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Actions */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href={switchHref}
              className="px-3 py-2 text-sm font-medium text-mizan-slate hover:text-mizan-green transition-colors rounded-lg hover:bg-mizan-green-pale"
            >
              {dict.nav.langSwitch}
            </Link>
            <Link
              href={`/${locale}/login`}
              className="px-4 py-2 text-sm font-medium text-mizan-green hover:bg-mizan-green-pale rounded-lg transition-colors font-arabic"
            >
              {dict.nav.login}
            </Link>
            <Link
              href={`/${locale}/signup`}
              className="px-5 py-2.5 text-sm font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-lg transition-colors shadow-sm font-arabic"
            >
              {dict.nav.signup}
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-mizan-ink"
            aria-label="Menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 animate-fade-in">
            <div className="flex flex-col gap-2 pt-2">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-4 py-3 text-sm font-medium text-mizan-slate hover:bg-mizan-green-pale hover:text-mizan-green rounded-lg transition-colors font-arabic"
                >
                  {item.label}
                </Link>
              ))}
              <div className="border-t border-gray-100 mt-2 pt-3 flex flex-col gap-2">
                <Link
                  href={switchHref}
                  className="px-4 py-2 text-sm font-medium text-mizan-slate font-latin"
                >
                  {dict.nav.langSwitch}
                </Link>
                <Link
                  href={`/${locale}/signup`}
                  className="px-5 py-3 text-sm font-semibold text-white bg-mizan-green rounded-lg text-center font-arabic"
                >
                  {dict.nav.signup}
                </Link>
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
