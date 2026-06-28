"use client";

import { useState, useEffect } from "react";
import { useWatchlist } from "@/hooks/useWatchlist";
import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import StarButton from "@/components/StarButton";
import Link from "next/link";

interface WatchlistProps {
  dict: ReturnType<typeof getDict>;
  locale: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Fetch fresh screening data for a watched stock */
async function refreshStock(ticker: string): Promise<{ verdict: string; verdict_detail: string } | null> {
  try {
    const res = await fetch(`${API_BASE}/api/stocks/${encodeURIComponent(ticker)}`);
    if (res.ok) {
      const data = await res.json();
      return { verdict: data.verdict, verdict_detail: data.verdict_detail };
    }
  } catch {
    // ignore
  }
  return null;
}

function verdictBadge(verdict: string) {
  if (verdict === "COMPLIANT")
    return { bg: "bg-mizan-green", text: "text-white", soft: "bg-mizan-green-pale" };
  if (verdict === "COMPLIANT_WITH_OVERLAY" || verdict === "COMPLIANT_WITH_PURIFICATION")
    return { bg: "bg-mizan-gold", text: "text-white", soft: "bg-amber-50" };
  return { bg: "bg-red-500", text: "text-white", soft: "bg-red-50" };
}

function verdictLabel(verdict: string, locale: string): string {
  if (verdict === "COMPLIANT") return locale === "ar" ? "حلال مؤكد" : "Halal";
  if (verdict === "COMPLIANT_WITH_OVERLAY" || verdict === "COMPLIANT_WITH_PURIFICATION")
    return locale === "ar" ? "يتطلب تنقية" : "Purification";
  return locale === "ar" ? "غير متوافق" : "Non-compliant";
}

export default function WatchlistPage({ dict, locale }: WatchlistProps) {
  useLocaleAttrs(locale as Locale, getDirection(locale));
  const { items, remove, clear, loaded } = useWatchlist();
  const [refreshing, setRefreshing] = useState(false);
  const [verdictOverrides, setVerdictOverrides] = useState<Record<string, { verdict: string; verdict_detail: string }>>({});

  const handleRefresh = async () => {
    setRefreshing(true);
    const updates: Record<string, { verdict: string; verdict_detail: string }> = {};
    await Promise.all(
      items.map(async (item) => {
        const fresh = await refreshStock(item.ticker);
        if (fresh && fresh.verdict !== item.verdict) {
          updates[item.ticker] = fresh;
        }
      })
    );
    setVerdictOverrides(updates);
    setRefreshing(false);
  };

  // Count by verdict
  const compliant = items.filter((i) => {
    const v = verdictOverrides[i.ticker]?.verdict ?? i.verdict;
    return v === "COMPLIANT";
  }).length;
  const purification = items.filter((i) => {
    const v = verdictOverrides[i.ticker]?.verdict ?? i.verdict;
    return v === "COMPLIANT_WITH_OVERLAY" || v === "COMPLIANT_WITH_PURIFICATION";
  }).length;
  const nonCompliant = items.filter((i) => {
    const v = verdictOverrides[i.ticker]?.verdict ?? i.verdict;
    return v !== "COMPLIANT" && v !== "COMPLIANT_WITH_OVERLAY" && v !== "COMPLIANT_WITH_PURIFICATION";
  }).length;

  const hasChanges = Object.keys(verdictOverrides).length > 0;

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="min-h-screen pt-20 md:pt-24 bg-mizan-cream">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">

          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <h1 className="text-3xl md:text-4xl font-bold text-mizan-ink font-arabic flex items-center gap-3">
                  <svg className="w-8 h-8 text-mizan-gold" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                  </svg>
                  {locale === "ar" ? "قائمة المراقبة" : "My Watchlist"}
                </h1>
                <p className="text-mizan-slate mt-2 font-arabic">
                  {locale === "ar"
                    ? "تتبع الأسهم التي تهمك وأعد فحصها بسهولة"
                    : "Track stocks you're interested in and re-screen with one click"}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRefresh}
                  disabled={refreshing || items.length === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-mizan-green text-white hover:bg-mizan-green-dark disabled:opacity-50 transition-colors font-arabic"
                >
                  <svg className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  {refreshing
                    ? locale === "ar" ? "جاري التحديث..." : "Refreshing..."
                    : locale === "ar" ? "إعادة الفحص" : "Re-screen All"}
                </button>
                {items.length > 0 && (
                  <button
                    onClick={() => {
                      if (confirm(locale === "ar" ? "هل تريد حذف جميع الأسهم؟" : "Remove all stocks?")) {
                        clear();
                      }
                    }}
                    className="px-3 py-2 text-sm font-medium rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors font-arabic"
                  >
                    {locale === "ar" ? "مسح الكل" : "Clear All"}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Empty state */}
          {loaded && items.length === 0 && (
            <div className="text-center py-20">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-mizan-gold/10 mb-6">
                <svg className="w-10 h-10 text-mizan-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-mizan-ink mb-2 font-arabic">
                {locale === "ar" ? "قائمتك فارغة" : "Your watchlist is empty"}
              </h2>
              <p className="text-mizan-slate mb-6 font-arabic">
                {locale === "ar"
                  ? "تصفح الأسهم الحالية وانقر على النجمة لإضافتها هنا"
                  : "Browse halal stocks and click the star to add them here"}
              </p>
              <Link
                href={`/${locale}#discover`}
                className="inline-flex items-center gap-2 px-6 py-3 bg-mizan-green text-white rounded-lg font-medium hover:bg-mizan-green-dark transition-colors font-arabic"
              >
                {locale === "ar" ? "تصفح الأسهم الحلال" : "Browse Halal Stocks"}
              </Link>
            </div>
          )}

          {/* Stock list */}
          {loaded && items.length > 0 && (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-3 md:gap-4 mb-8">
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 text-center">
                  <div className="text-3xl font-bold text-mizan-green">{compliant}</div>
                  <div className="text-xs text-mizan-slate mt-1 font-arabic">
                    {locale === "ar" ? "حلال مؤكد" : "Compliant"}
                  </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 text-center">
                  <div className="text-3xl font-bold text-mizan-gold-dark">{purification}</div>
                  <div className="text-xs text-mizan-slate mt-1 font-arabic">
                    {locale === "ar" ? "يتطلب تنقية" : "Purification"}
                  </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 text-center">
                  <div className="text-3xl font-bold text-red-500">{nonCompliant}</div>
                  <div className="text-xs text-mizan-slate mt-1 font-arabic">
                    {locale === "ar" ? "غير متوافق" : "Non-compliant"}
                  </div>
                </div>
              </div>

              {/* Change alert */}
              {hasChanges && (
                <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                  <div className="flex items-center gap-2 text-amber-800 font-arabic">
                    <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span>
                      {locale === "ar"
                        ? `${Object.keys(verdictOverrides).length} سهم تغير حكمه الشرعي منذ آخر فحص`
                        : `${Object.keys(verdictOverrides).length} stock(s) had verdict changes since you added them`}
                    </span>
                  </div>
                </div>
              )}

              {/* Stock table/cards */}
              <div className="space-y-3">
                {items.map((item) => {
                  const effectiveVerdict = verdictOverrides[item.ticker]?.verdict ?? item.verdict;
                  const styles = verdictBadge(effectiveVerdict);
                  const changed = !!verdictOverrides[item.ticker];

                  return (
                    <div
                      key={item.ticker}
                      className="bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow p-4 flex items-center gap-4"
                    >
                      {/* Star/remove */}
                      <StarButton
                        ticker={item.ticker}
                        name_en={item.name_en}
                        name_ar={item.name_ar}
                        sector_en={item.sector_en}
                        sector_ar={item.sector_ar}
                        verdict={item.verdict}
                        locale={locale}
                        size="sm"
                      />

                      {/* Info */}
                      <Link href={`/${locale}/stock/${item.ticker}`} className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-mizan-ink font-arabic truncate">
                            {locale === "ar" ? item.name_ar : item.name_en}
                          </h3>
                          <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded text-mizan-slate">
                            {item.ticker}
                          </span>
                        </div>
                        <p className="text-xs text-mizan-slate mt-0.5 font-arabic">
                          {locale === "ar" ? item.sector_ar : item.sector_en}
                        </p>
                      </Link>

                      {/* Verdict badge */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {changed && (
                          <span className="text-xs text-amber-600 font-arabic" title={locale === "ar" ? "تغير" : "Changed"}>
                            ●
                          </span>
                        )}
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${styles.bg} ${styles.text} font-arabic`}>
                          {verdictLabel(effectiveVerdict, locale)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Footer note */}
              <p className="text-center text-xs text-mizan-slate mt-8 font-arabic">
                {locale === "ar"
                  ? "تُحفظ قائمة المراقبة على جهازك فقط. أعد فحص الأسهم بانتظام بعد كل موسم نتائج."
                  : "Your watchlist is stored locally on your device. Re-screen stocks regularly after each earnings season."}
              </p>
            </>
          )}

          {/* Loading */}
          {!loaded && (
            <div className="text-center py-20">
              <div className="inline-block w-8 h-8 border-4 border-mizan-green border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
