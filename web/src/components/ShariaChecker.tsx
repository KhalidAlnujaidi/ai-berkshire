"use client";

import { useState, useEffect } from "react";
import type { Dict } from "@/i18n/ar";

interface ShariaCheckerProps {
  dict: Dict;
  locale: string;
}

// API response shape from backend
interface RatioResult {
  value: number;
  threshold: string;
  passed: boolean;
}

interface ShariaApiResponse {
  company: string;
  ticker: string;
  sector: string;
  name_ar: string;
  sector_ar: string;
  verdict: string;
  verdict_ar: string;
  verdict_detail: string;
  qualitative_screen: {
    compliant: boolean;
    category: string;
    notes: string;
  };
  quantitative_screen: Record<string, RatioResult | boolean> | null;
}

// Fallback demo data when API is unavailable (e.g. static export)
const FALLBACK_STOCKS: Record<string, Partial<ShariaApiResponse>> = {
  "1120": {
    company: "Al Rajhi Bank",
    ticker: "1120",
    name_ar: "مصرف الراجحي",
    sector: "Islamic Banking",
    sector_ar: "الخدمات المصرفية الإسلامية",
    verdict: "COMPLIANT",
    verdict_ar: "متوافق",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
  "2222": {
    company: "Saudi Aramco",
    ticker: "2222",
    name_ar: "أرامكو السعودية",
    sector: "Energy",
    sector_ar: "الطاقة",
    verdict: "COMPLIANT",
    verdict_ar: "متوافق",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
  "7010": {
    company: "STC Group",
    ticker: "7010",
    name_ar: "مجموعة إس تي سي",
    sector: "Telecommunications",
    sector_ar: "الاتصالات",
    verdict: "COMPLIANT",
    verdict_ar: "متوافق",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
  "2010": {
    company: "SABIC",
    ticker: "2010",
    name_ar: "سابك",
    sector: "Petrochemicals",
    sector_ar: "البتروكيماويات",
    verdict: "COMPLIANT_WITH_OVERLAY",
    verdict_ar: "متوافق مع ملاحظات",
    verdict_detail: "Permitted business. Monitor for impermissible income streams.",
  },
  "1180": {
    company: "Saudi National Bank (SNB)",
    ticker: "1180",
    name_ar: "بنك الأهلي السعودي",
    sector: "Conventional Banking",
    sector_ar: "الخدمات المصرفية التقليدية",
    verdict: "NON_COMPLIANT",
    verdict_ar: "غير متوافق",
    verdict_detail: "Core business is conventional (interest-based) banking. Hard fail.",
  },
};

// Determine API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ShariaChecker({ dict, locale }: ShariaCheckerProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ShariaApiResponse | null>(null);
  const [error, setError] = useState("");

  // Listen for prefill events from HalalStocksGrid
  useEffect(() => {
    function handlePrefill(e: Event) {
      const detail = (e as CustomEvent).detail;
      if (detail?.ticker) {
        setQuery(detail.ticker);
        handleCheck(detail.ticker);
      }
    }
    window.addEventListener("prefill-stock", handlePrefill);
    return () => window.removeEventListener("prefill-stock", handlePrefill);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCheck(stockKey?: string) {
    const q = (stockKey || query).trim();
    if (!q) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/stocks/${encodeURIComponent(q)}`);
      if (res.ok) {
        const data: ShariaApiResponse = await res.json();
        setResult(data);
      } else if (res.status === 404) {
        // Try search endpoint
        const searchRes = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(q)}`);
        if (searchRes.ok) {
          const results = await searchRes.json();
          if (results.length > 0) {
            // Fetch full screening for first match
            const fullRes = await fetch(`${API_BASE}/api/stocks/${results[0].ticker}`);
            if (fullRes.ok) {
              setResult(await fullRes.json());
            } else {
              setError(locale === "ar" ? "لم يتم العثور على السهم." : "Stock not found.");
            }
          } else {
            setError(locale === "ar" ? "لم يتم العثور على السهم." : "Stock not found.");
          }
        } else {
          setError(locale === "ar" ? "لم يتم العثور على السهم." : "Stock not found.");
        }
      }
    } catch {
      // API not available — use fallback demo data
      const fallback = FALLBACK_STOCKS[q];
      if (fallback) {
        setResult(fallback as ShariaApiResponse);
      } else {
        // Try name match in fallback
        for (const [, s] of Object.entries(FALLBACK_STOCKS)) {
          if (
            (s.name_ar && s.name_ar.includes(q)) ||
            (s.company && s.company.toLowerCase().includes(q.toLowerCase()))
          ) {
            setResult(s as ShariaApiResponse);
            return;
          }
        }
        setError(
          locale === "ar"
            ? "لم يتم العثور على السهم. جرّب أحد الأمثلة أدناه."
            : "Stock not found. Try one of the examples below."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  const verdictColor =
    result?.verdict === "COMPLIANT"
      ? "green"
      : result?.verdict === "COMPLIANT_WITH_OVERLAY" || result?.verdict === "COMPLIANT_WITH_PURIFICATION"
      ? "gold"
      : "red";

  const isNonCompliant = result?.verdict === "NON_COMPLIANT";

  // Extract ratio results from API response
  const ratios = result?.quantitative_screen
    ? Object.entries(result.quantitative_screen)
        .filter(([, val]) => typeof val === "object" && val !== null && "value" in val)
        .map(([key, val]) => {
          const r = val as RatioResult;
          return {
            label: ratioLabel(key, locale),
            value: `${r.value.toFixed(2)}%`,
            threshold: r.threshold,
            pass: r.passed,
          };
        })
    : [];

  return (
    <section id="checker" className="py-20 md:py-28 bg-gradient-to-b from-white to-mizan-green-pale/30">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-4 font-arabic">
            {dict.checker.title}
          </h2>
          <p className="text-lg text-mizan-slate font-arabic">{dict.checker.subtitle}</p>
        </div>

        {/* Search box */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 md:p-8">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCheck()}
              placeholder={dict.checker.placeholder}
              className="flex-1 px-5 py-4 text-base rounded-xl border-2 border-gray-200 focus:border-mizan-green focus:ring-0 focus:outline-none transition-colors font-arabic"
              dir={locale === "ar" ? "rtl" : "ltr"}
            />
            <button
              onClick={() => handleCheck()}
              disabled={loading || !query.trim()}
              className="px-8 py-4 text-base font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-arabic whitespace-nowrap"
            >
              {loading ? dict.checker.checking : dict.checker.button}
            </button>
          </div>

          {/* Examples */}
          <div className="flex flex-wrap items-center gap-2 mt-4">
            <span className="text-sm text-mizan-slate font-arabic">{dict.checker.tryExample}</span>
            {[
              { key: "1120", label: dict.checker.examples.rajhi },
              { key: "2222", label: dict.checker.examples.aramco },
              { key: "7010", label: dict.checker.examples.stc },
              { key: "2010", label: dict.checker.examples.sabic },
            ].map((ex) => (
              <button
                key={ex.key}
                onClick={() => {
                  setQuery(ex.label);
                  handleCheck(ex.key);
                }}
                className="px-3 py-1.5 text-xs font-medium text-mizan-green bg-mizan-green-pale hover:bg-mizan-green/10 rounded-lg transition-colors font-arabic"
              >
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm font-arabic animate-scale-in">
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="mt-8 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden animate-scale-in">
            {/* Verdict header */}
            <div
              className={`px-6 py-5 ${
                verdictColor === "green"
                  ? "bg-mizan-green/10"
                  : verdictColor === "gold"
                  ? "bg-amber-50"
                  : "bg-red-50"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-mizan-slate font-arabic">{result.company}</p>
                  {result.name_ar && (
                    <p className="text-xl font-bold text-mizan-ink font-arabic">{result.name_ar}</p>
                  )}
                </div>
                <div className="text-right">
                  <span
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold ${
                      verdictColor === "green"
                        ? "bg-mizan-green text-white"
                        : verdictColor === "gold"
                        ? "bg-amber-500 text-white"
                        : "bg-red-500 text-white"
                    }`}
                  >
                    {verdictColor === "green"
                      ? "✓"
                      : verdictColor === "gold"
                      ? "⚠"
                      : "✗"}
                    {locale === "ar" ? result.verdict_ar : result.verdict.replace(/_/g, " ")}
                  </span>
                </div>
              </div>
            </div>

            {/* Non-compliant warning banner */}
            {isNonCompliant && (
              <div className="px-6 py-3 bg-red-500/10 border-b border-red-100">
                <p className="text-sm text-red-700 font-arabic flex items-center gap-2">
                  <span className="text-lg">🚫</span>
                  {locale === "ar"
                    ? "هذا السهم غير متوافق مع الشريعة الإسلامية. لا يُنصح بالاستثمار فيه للمستثمر المسلم."
                    : "This stock is NOT Sharia-compliant. Muslim investors should avoid it."}
                </p>
              </div>
            )}

            {/* Detail */}
            <div className="px-6 py-4">
              <p className="text-sm text-mizan-slate font-arabic mb-4">{result.verdict_detail}</p>

              {/* Sector screen */}
              {result.qualitative_screen && (
                <div className="mb-4">
                  <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2 font-arabic">
                    {dict.checker.sectorScreen}
                  </h4>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                        result.qualitative_screen.compliant
                          ? "bg-mizan-green/20 text-mizan-green"
                          : "bg-red-100 text-red-500"
                      }`}
                    >
                      {result.qualitative_screen.compliant ? "✓" : "✗"}
                    </span>
                    <span className="text-sm text-mizan-slate font-arabic">
                      {result.qualitative_screen.notes}
                    </span>
                  </div>
                </div>
              )}

              {/* Ratios */}
              {ratios.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2 font-arabic">
                    {dict.checker.ratioScreen}
                  </h4>
                  <div className="space-y-2">
                    {ratios.map((ratio, i) => (
                      <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                              ratio.pass
                                ? "bg-mizan-green/20 text-mizan-green"
                                : "bg-red-100 text-red-500"
                            }`}
                          >
                            {ratio.pass ? "✓" : "✗"}
                          </span>
                          <span className="text-sm text-mizan-slate font-arabic">{ratio.label}</span>
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-mono font-medium text-mizan-ink">
                            {ratio.value}
                          </span>
                          <span className="text-xs text-gray-400 ml-1">/ {ratio.threshold}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

// Helper: human-readable ratio labels
function ratioLabel(key: string, locale: string): string {
  const labels: Record<string, { en: string; ar: string }> = {
    debt_to_assets: { en: "Debt / Total Assets", ar: "الدين / إجمالي الأصول" },
    debt_to_market_cap: { en: "Debt / Market Cap", ar: "الدين / القيمة السوقية" },
    interest_bearing_investments_to_assets: {
      en: "Interest-Bearing Investments / Assets",
      ar: "استثمارات Bearing الفائدة / الأصول",
    },
    interest_bearing_investments_to_market_cap: {
      en: "Interest-Bearing Investments / Market Cap",
      ar: "استثمارات Bearing الفائدة / القيمة السوقية",
    },
    receivables_to_total: {
      en: "Accounts Receivable / (Cash + Receivables)",
      ar: "الذمم المدينة / (النقد + الذمم)",
    },
    non_compliant_income: {
      en: "Non-Compliant Income / Revenue",
      ar: "الدخل غير المتوافق / الإيرادات",
    },
  };
  const entry = labels[key];
  if (!entry) return key;
  return locale === "ar" ? entry.ar : entry.en;
}
