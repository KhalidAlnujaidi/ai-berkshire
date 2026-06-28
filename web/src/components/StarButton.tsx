"use client";

import { useWatchlist, type WatchlistItem } from "@/hooks/useWatchlist";
import Link from "next/link";

interface StarButtonProps {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
  verdict: string;
  locale: string;
  size?: "sm" | "md";
}

/**
 * Star button to add/remove a stock from the watchlist.
 * Renders consistently in both list views and detail pages.
 */
export default function StarButton({
  ticker,
  name_en,
  name_ar,
  sector_en,
  sector_ar,
  verdict,
  locale,
  size = "md",
}: StarButtonProps) {
  const { isInWatchlist, toggle } = useWatchlist();
  const starred = isInWatchlist(ticker);

  const sizeClasses =
    size === "sm" ? "w-8 h-8" : "w-10 h-10";
  const iconSize = size === "sm" ? "w-4 h-4" : "w-5 h-5";

  return (
    <button
      type="button"
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggle({ ticker, name_en, name_ar, sector_en, sector_ar, verdict });
      }}
      className={`${sizeClasses} flex-shrink-0 flex items-center justify-center rounded-full transition-all duration-200 ${
        starred
          ? "bg-mizan-gold/20 text-mizan-gold-dark hover:bg-mizan-gold/30"
          : "bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-mizan-gold-dark"
      }`}
      aria-label={
        starred
          ? locale === "ar"
            ? "إزالة من قائمة المراقبة"
            : "Remove from watchlist"
          : locale === "ar"
            ? "إضافة إلى قائمة المراقبة"
            : "Add to watchlist"
      }
      title={
        starred
          ? locale === "ar"
            ? "إزالة من قائمة المراقبة"
            : "Remove from watchlist"
          : locale === "ar"
            ? "إضافة إلى قائمة المراقبة"
            : "Add to watchlist"
      }
    >
      <svg
        className={`${iconSize} ${starred ? "fill-current" : "fill-none"}`}
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
        />
      </svg>
    </button>
  );
}

/**
 * Floating watchlist badge for the navbar.
 * Shows count and links to the watchlist page.
 */
export function WatchlistBadge({ locale }: { locale: string }) {
  const { count } = useWatchlist();

  if (count === 0) return null;

  return (
    <Link
      href={`/${locale}/watchlist`}
      className="relative flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg bg-mizan-gold/10 text-mizan-gold-dark hover:bg-mizan-gold/20 transition-colors font-arabic"
    >
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
      </svg>
      <span>{count}</span>
    </Link>
  );
}
