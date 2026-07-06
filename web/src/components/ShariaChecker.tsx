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
    verdict_detail: "Islamic banking model. Debt/assets 58% — under AAOIFI threshold of 70%. No conventional interest income.",
  },
  "2222": {
    company: "Saudi Aramco",
    ticker: "2222",
    name_ar: "أرامكو السعودية",
    sector: "Energy",
    sector_ar: "الطاقة",
    verdict: "COMPLIANT",
    verdict_ar: "متوافق",
    verdict_detail: "Energy sector business permissible. Debt/assets 2.3% — well below 70% limit. Minimal interest-bearing investments.",
  },
  "7010": {
    company: "STC Group",
    ticker: "7010",
    name_ar: "مجموعة إس تي سي",
    sector: "Telecommunications",
    sector_ar: "الاتصالات",
    verdict: "COMPLIANT",
    verdict_ar: "متوافق",
    verdict_detail: "Telecom permissible sector. Debt/assets 42% within AAOIFI limits. Interest income < 5% of total revenue.",
  },
  "2010": {
    company: "SABIC",
    ticker: "2010",
    name_ar: "سابك",
    sector: "Petrochemicals",
    sector_ar: "البتروكيماويات",
    verdict: "COMPLIANT",
    verdict_ar: "متوافق",
    verdict_detail: "Petrochemicals sector is permissible. All financial ratios pass AAOIFI Standard No. 21 thresholds.",
  },
  "1180": {
    company: "Saudi National Bank (SNB)",
    ticker: "1180",
    name_ar: "بنك الأهلي السعودي",
    sector: "Conventional Banking",
    sector_ar: "الخدمات المصرفية التقليدية",
    verdict: "NON-COMPLIANT",
    verdict_ar: "غير متوافق",
    verdict_detail: "Core business is conventional (interest-based) banking. Hard fail — interest income is the primary revenue stream.",
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
  const isNonCompliant = result?.verdict === "NON_COMPLIANT" || result?.verdict === "NON-COMPLIANT";

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
                  setQuery(ex.key);
                  handleCheck(ex.key);
                }}
                className="px-3 py-1.5 text-xs font-medium bg-mizan-green-pale text-mizan-green rounded-lg hover:bg-mizan-green/20 transition-colors font-arabic"
              >
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-8 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-center font-arabic">
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="mt-8 bg-white rounded-2xl shadow-xl border border-gray-100 p-6 md:p-8">
            {/* Company header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <span className="text-xs font-mono text-mizan-slate">{result.ticker}</span>
                <h3 className="text-2xl font-bold text-mizan-ink font-arabic">
                  {locale === "ar" ? result.name_ar : result.company}
                </h3>
                <p className="text-sm text-mizan-slate font-arabic">
                  {locale === "ar" ? result.sector_ar : result.sector}
                </p>
              </div>

              {/* Verdict badge */}
              <div
                className={`px-5 py-2 rounded-xl text-sm font-bold text-white ${
                  verdictColor === "green"
                    ? "bg-mizan-green"
                    : verdictColor === "gold"
                    ? "bg-mizan-gold text-mizan-ink"
                    : "bg-red-500"
                }`}
              >
                {result.verdict === "COMPLIANT"
                  ? dict.checker.resultCompliant
                  : result.verdict === "COMPLIANT_WITH_OVERLAY" || result.verdict === "COMPLIANT_WITH_PURIFICATION"
                  ? dict.checker.resultOverlay
                  : result.verdict === "NON_COMPLIANT" || result.verdict === "NON-COMPLIANT"
                  ? dict.checker.resultNonCompliant
                  : result.verdict_ar}
              </div>
            </div>

            {/* Verdict detail — specific, not boilerplate */}
            <div className="mb-4 p-4 rounded-xl bg-gray-50 border border-gray-100">
              <p className="text-sm text-mizan-slate leading-relaxed font-arabic">
                {result.verdict_detail}
              </p>
            </div>

            {/* Warning explanation for overlay/purification stocks */}
            {(result.verdict === "COMPLIANT_WITH_OVERLAY" || result.verdict === "COMPLIANT_WITH_PURIFICATION") && (
              <div className="mb-4 p-4 rounded-xl bg-amber-50 border border-amber-200">
                <div className="flex items-start gap-2">
                  <span className="text-amber-600 text-lg">⚠️</span>
                  <div>
                    <p className="text-sm font-semibold text-amber-800 font-arabic mb-1">
                      {dict.checker.warningTitle}
                    </p>
                    <p className="text-sm text-amber-700 leading-relaxed font-arabic">
                      {dict.checker.warningExplanation}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Non-compliant explanation */}
            {(result.verdict === "NON_COMPLIANT" || result.verdict === "NON-COMPLIANT") && (
              <div className="mb-4 p-4 rounded-xl bg-red-50 border border-red-200">
                <div className="flex items-start gap-2">
                  <span className="text-red-600 text-lg">❌</span>
                  <div>
                    <p className="text-sm font-semibold text-red-800 font-arabic mb-1">
                      {dict.checker.nonCompliantTitle}
                    </p>
                    <p className="text-sm text-red-700 leading-relaxed font-arabic">
                      {dict.checker.nonCompliantExplanation}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Qualitative Screen */}
            <div className="mb-6">
              <h4 className="text-sm font-bold text-mizan-ink mb-3 font-arabic">
                {dict.checker.sectorScreen}
              </h4>
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    result.qualitative_screen?.compliant ? "bg-mizan-green" : "bg-red-500"
                  }`}
                />
                <span className="text-sm text-mizan-slate font-arabic">
                  {result.qualitative_screen?.compliant
                    ? (locale === "ar" ? "نشاط حلال: " : "Permissible business: ")
                    : (locale === "ar" ? "نشاط غير جائز: " : "Impermissible business: ")}
                  {result.qualitative_screen?.category}
                </span>
              </div>
              {result.qualitative_screen?.notes && (
                <p className="text-xs text-mizan-slate/70 ml-4 font-arabic">
                  {result.qualitative_screen.notes}
                </p>
              )}
            </div>

            {/* Quantitative Screen */}
            {ratios.length > 0 && (
              <div>
                <h4 className="text-sm font-bold text-mizan-ink mb-3 font-arabic">
                  {dict.checker.ratioScreen}
                </h4>
                <div className="space-y-2">
                  {ratios.map((r, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 rounded-lg bg-gray-50"
                    >
                      <span className="text-sm text-mizan-slate font-arabic">{r.label}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-mono text-mizan-ink">{r.value}</span>
                        <span className="text-xs text-mizan-slate/60 font-arabic">
                          ({r.threshold})
                        </span>
                        <span
                          className={`text-sm ${
                            r.pass ? "text-mizan-green" : "text-red-500"
                          }`}
                        >
                          {r.pass ? "✓" : "✗"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Final verdict */}
            <div className="mt-6 pt-6 border-t border-gray-100">
              <h4 className="text-sm font-bold text-mizan-ink mb-2 font-arabic">
                {dict.checker.verdict}
              </h4>
              <p
                className={`text-base font-semibold ${
                  verdictColor === "green"
                    ? "text-mizan-green"
                    : verdictColor === "gold"
                    ? "text-mizan-gold-dark"
                    : "text-red-500"
                } font-arabic`}
              >
                {result.verdict === "COMPLIANT"
                  ? dict.checker.verdicts.compliant
                  : result.verdict === "COMPLIANT_WITH_OVERLAY" || result.verdict === "COMPLIANT_WITH_PURIFICATION"
                  ? dict.checker.verdicts.overlay
                  : dict.checker.verdicts.nonCompliant}
              </p>
            </div>

            {/* AI Disclaimer */}
            <div className="mt-4 p-3 rounded-lg bg-gray-50 border border-gray-100">
              <p className="text-xs text-mizan-slate/60 font-arabic italic">
                {dict.checker.aiDisclaimer}
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

// Ratio label helper (local to this component)
function ratioLabel(key: string, locale: string): string {
  const map: Record<string, string> = {
    debt_to_assets: locale === "ar" ? "الدين / الأصول" : "Debt / Assets",
    debt_to_market_cap: locale === "ar" ? "الدين / القيمة السوقية" : "Debt / Market Cap",
    interest_bearing_investments_to_assets: locale === "ar" ? "الاستثمارات الربوية / الأصول" : "Interest Inv. / Assets",
    interest_bearing_investments_to_market_cap: locale === "ar" ? "الاستثمارات الربوية / القيمة السوقية" : "Interest Inv. / Market Cap",
    receivables_to_total: locale === "ar" ? "المدينون / الإجمالي" : "Receivables / Total",
    non_compliant_income: locale === "ar" ? "الدخل غير المشروع" : "Non-Compliant Income",
  };
  return map[key] || key;
}