"use client";

import { use, useState, useEffect } from "react";
import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import StarButton from "@/components/StarButton";
import Footer from "@/components/Footer";
import Link from "next/link";

// ── Types matching backend response ────────────────────────────────────────

interface RatioResult {
  value: number;
  threshold: string;
  passed: boolean;
  label?: string;
  purification_needed?: boolean;
  purification_amount?: number;
}

interface QualitativeScreen {
  compliant: boolean;
  category: string;
  matched_rule?: string;
  notes: string;
}

type QuantitativeScreen = Record<string, RatioResult | boolean> | null;

interface StockDetail {
  company: string;
  ticker: string;
  sector: string;
  name_ar: string;
  sector_ar: string;
  verdict: string;
  verdict_ar: string;
  verdict_detail: string;
  qualitative_screen: QualitativeScreen;
  quantitative_screen: QuantitativeScreen;
  standard: string;
  market: string;
  currency: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function verdictStyles(verdict: string) {
  if (verdict === "COMPLIANT")
    return { bg: "bg-mizan-green", text: "text-white", ring: "ring-mizan-green", soft: "bg-mizan-green-pale", label: "✓" };
  if (verdict === "COMPLIANT_WITH_OVERLAY" || verdict === "COMPLIANT_WITH_PURIFICATION")
    return { bg: "bg-mizan-gold", text: "text-white", ring: "ring-mizan-gold", soft: "bg-amber-50", label: "⚠" };
  return { bg: "bg-red-500", text: "text-white", ring: "ring-red-500", soft: "bg-red-50", label: "✗" };
}

function formatPercent(val: number): string {
  return `${val.toFixed(2)}%`;
}

/** Human-friendly label for each ratio key */
function ratioLabel(key: string, locale: string): string {
  const labels: Record<string, { en: string; ar: string }> = {
    debt_to_assets: { en: "Interest-bearing Debt / Total Assets", ar: "الدين بفائدة / إجمالي الأصول" },
    debt_to_market_cap: { en: "Interest-bearing Debt / Market Cap", ar: "الدين بفائدة / القيمة السوقية" },
    interest_bearing_investments_to_assets: { en: "Interest-bearing Investments / Assets", ar: "استثمارات بفائدة / الأصول" },
    interest_bearing_investments_to_market_cap: { en: "Interest-bearing Investments / Market Cap", ar: "استثمارات بفائدة / القيمة السوقية" },
    receivables_to_total: { en: "Accounts Receivable / (Cash + Receivables)", ar: "الذمم المدينة / (نقد + ذمم)" },
    non_compliant_income: { en: "Non-compliant Income / Revenue", ar: "الدخل غير المتوافق / الإيرادات" },
  };
  const entry = labels[key];
  if (!entry) return key;
  return locale === "ar" ? entry.ar : entry.en;
}

// ── Page Component ─────────────────────────────────────────────────────────

export default function StockDetailPage({
  params,
}: {
  params: Promise<{ locale: string; ticker: string }>;
}) {
  const { locale: localeStr, ticker } = use(params);
  const locale = localeStr as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);

  useLocaleAttrs(locale, dir);

  const [stock, setStock] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchStock() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/api/stocks/${encodeURIComponent(ticker)}`);
        if (res.ok) {
          setStock(await res.json());
        } else if (res.status === 404) {
          setError(locale === "ar" ? "لم يتم العثور على السهم" : "Stock not found");
        } else {
          setError(locale === "ar" ? "خطأ في الخادم" : "Server error");
        }
      } catch {
        setError(locale === "ar" ? "تعذر الاتصال بالخادم" : "Cannot connect to server");
      } finally {
        setLoading(false);
      }
    }
    fetchStock();
  }, [ticker, locale]);

  const ratios = stock?.quantitative_screen
    ? Object.entries(stock.quantitative_screen)
        .filter(([, val]) => typeof val === "object" && val !== null && "value" in val)
        .map(([key, val]) => {
          const r = val as RatioResult;
          return { key, ...r };
        })
    : [];

  const styles = stock ? verdictStyles(stock.verdict) : null;

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="min-h-screen pt-20 md:pt-24 bg-mizan-cream">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">

          {/* Back link */}
          <Link
            href={`/${locale}#discover`}
            className="inline-flex items-center gap-1.5 text-sm text-mizan-slate hover:text-mizan-green transition-colors mb-6 font-arabic"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={dir === "rtl" ? "M9 5l7 7-7 7" : "M15 19l-7-7 7-7"} />
            </svg>
            {locale === "ar" ? "العودة للأسهم الحلال" : "Back to Halal Stocks"}
          </Link>

          {/* Loading */}
          {loading && (
            <div className="text-center py-20">
              <div className="inline-block w-10 h-10 border-4 border-mizan-green border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-mizan-slate font-arabic">
                {locale === "ar" ? "جاري فحص السهم..." : "Screening stock..."}
              </p>
            </div>
          )}

          {/* Error */}
          {error && !loading && (
            <div className="text-center py-20">
              <div className="text-5xl mb-4">🔍</div>
              <p className="text-xl text-mizan-slate font-arabic mb-2">{error}</p>
              <Link href={`/${locale}#checker`} className="text-mizan-green hover:underline font-arabic">
                {locale === "ar" ? "جرّب فاحص الشريعة" : "Try the Sharia Checker"}
              </Link>
            </div>
          )}

          {/* Stock Detail */}
          {stock && !loading && styles && (
            <div className="space-y-6 animate-fade-in-up">

              {/* Header card */}
              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
                <div className={`${styles.bg} px-6 py-8 md:px-8 md:py-10`}>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h1 className="text-2xl md:text-3xl font-bold text-white font-arabic">
                        {locale === "ar" ? stock.name_ar : stock.company}
                      </h1>
                      <div className="flex items-center gap-3 mt-2 text-white/80 text-sm">
                        <span className="font-mono bg-white/20 px-2 py-0.5 rounded">{stock.ticker}</span>
                        <span className="font-arabic">
                          {locale === "ar" ? stock.sector_ar : stock.sector}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-3">
                      <StarButton
                        ticker={stock.ticker}
                        name_en={stock.company}
                        name_ar={stock.name_ar}
                        sector_en={stock.sector}
                        sector_ar={stock.sector_ar}
                        verdict={stock.verdict}
                        locale={locale}
                      />
                      <div className="text-3xl">{styles.label}</div>
                    </div>
                  </div>
                </div>

                {/* Verdict banner */}
                <div className={`px-6 py-4 md:px-8 ${styles.soft} border-b border-gray-100`}>
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-wider text-mizan-slate mb-1 font-arabic">
                        {locale === "ar" ? "الحكم الشرعي" : "Sharia Verdict"}
                      </p>
                      <p className={`text-lg font-bold ${styles.bg === "bg-mizan-green" ? "text-mizan-green" : styles.bg === "bg-mizan-gold" ? "text-mizan-gold-dark" : "text-red-600"} font-arabic`}>
                        {locale === "ar" ? stock.verdict_ar : stock.verdict.replace(/_/g, " ")}
                      </p>
                    </div>
                    <div className="text-right text-xs text-mizan-slate">
                      <p className="font-arabic">{locale === "ar" ? "المعيار" : "Standard"}</p>
                      <p className="font-mono">{stock.standard}</p>
                    </div>
                  </div>
                  <p className="text-sm text-mizan-slate mt-2 font-arabic">{stock.verdict_detail}</p>
                </div>
              </div>

              {/* Qualitative Screen */}
              <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-6 md:p-8">
                <h2 className="text-lg font-bold text-mizan-ink mb-4 font-arabic flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${stock.qualitative_screen.compliant ? "bg-mizan-green" : "bg-red-500"}`} />
                  {locale === "ar" ? "الفحص النوعي (القطاع)" : "Qualitative Screen (Sector)"}
                </h2>
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 text-xs font-semibold rounded-full ${stock.qualitative_screen.compliant ? "bg-mizan-green-pale text-mizan-green" : "bg-red-50 text-red-600"}`}>
                      {stock.qualitative_screen.compliant
                        ? (locale === "ar" ? "مسموح" : "Permitted")
                        : (locale === "ar" ? "ممنوع" : "Prohibited")}
                    </span>
                    <span className="text-sm text-mizan-slate capitalize">
                      {stock.qualitative_screen.category}
                    </span>
                  </div>
                  <p className="text-sm text-mizan-slate font-arabic leading-relaxed">
                    {stock.qualitative_screen.notes}
                  </p>
                </div>
              </div>

              {/* Quantitative Screen */}
              {ratios.length > 0 && (
                <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-6 md:p-8">
                  <h2 className="text-lg font-bold text-mizan-ink mb-4 font-arabic flex items-center gap-2">
                    <span className={`w-3 h-3 rounded-full ${ratios.every((r) => r.passed) ? "bg-mizan-green" : "bg-mizan-gold"}`} />
                    {locale === "ar" ? "الفحص الكمي (النسب المالية)" : "Quantitative Screen (Financial Ratios)"}
                  </h2>

                  <div className="space-y-5">
                    {ratios.map((r) => {
                      const thresholdNum = parseFloat(String(r.threshold));
                      const pct = thresholdNum > 0 ? Math.min((r.value / thresholdNum) * 100, 100) : 0;
                      return (
                        <div key={r.key}>
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-sm font-medium text-mizan-ink font-arabic">
                              {ratioLabel(r.key, locale)}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className={`text-sm font-bold font-mono ${r.passed ? "text-mizan-green" : "text-red-500"}`}>
                                {formatPercent(r.value)}
                              </span>
                              <span className={`text-xs px-1.5 py-0.5 rounded ${r.passed ? "bg-mizan-green-pale text-mizan-green" : "bg-red-50 text-red-500"}`}>
                                {r.passed ? "✓" : "✗"}
                              </span>
                            </div>
                          </div>
                          {/* Threshold bar */}
                          <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-700 ${r.passed ? "bg-mizan-green" : "bg-red-400"}`}
                              style={{ width: `${pct}%` }}
                            />
                            {/* Threshold marker */}
                            <div
                              className="absolute top-0 h-full w-0.5 bg-mizan-ink/30"
                              style={{ left: "100%", transform: "translateX(-100%)" }}
                            />
                          </div>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-xs text-mizan-slate">
                              {locale === "ar" ? `الحد: ${r.threshold}%` : `Limit: ${r.threshold}%`}
                            </span>
                            {r.purification_needed && (
                              <span className="text-xs text-mizan-gold-dark font-arabic">
                                {locale === "ar" ? "⚠ يتطلب تنقية" : "⚠ Purification needed"}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Overall quantitative pass */}
                  <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between">
                    <span className="text-sm font-medium text-mizan-slate font-arabic">
                      {locale === "ar" ? "النتيجة الكلية" : "Overall Quantitative"}
                    </span>
                    <span className={`text-sm font-bold ${ratios.every((r) => r.passed) ? "text-mizan-green" : "text-mizan-gold-dark"}`}>
                      {ratios.every((r) => r.passed)
                        ? (locale === "ar" ? "✓ جميع النسب مطابقة" : "✓ All ratios pass")
                        : (locale === "ar" ? "⚠ بعض النسب تتجاوز الحد" : "⚠ Some ratios exceed threshold")}
                    </span>
                  </div>
                </div>
              )}

              {/* Meta info */}
              <div className="flex flex-wrap items-center gap-4 text-xs text-mizan-slate">
                <span className="flex items-center gap-1.5">
                  <span className="font-arabic">{locale === "ar" ? "السوق:" : "Market:"}</span>
                  <span className="font-mono uppercase">{stock.market}</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="font-arabic">{locale === "ar" ? "العملة:" : "Currency:"}</span>
                  <span className="font-mono">{stock.currency}</span>
                </span>
              </div>

              {/* CTA */}
              <div className="text-center pt-4">
                <Link
                  href={`/${locale}#checker`}
                  className="inline-block px-6 py-3 text-sm font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-colors font-arabic shadow-sm"
                >
                  {locale === "ar" ? "افحص سهماً آخر" : "Screen another stock"}
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
