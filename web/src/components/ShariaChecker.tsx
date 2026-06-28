"use client";

import { useState } from "react";
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
};

// Determine API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ShariaChecker({ dict, locale }: ShariaCheckerProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ShariaApiResponse | null>(null);
  const [error, setError] = useState("");

  const handleCheck = async (stockKey?: string) => {
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
  };

  const verdictColor =
    result?.verdict === "COMPLIANT"
      ? "green"
      : result?.verdict === "COMPLIANT_WITH_OVERLAY" || result?.verdict === "COMPLIANT_WITH_PURIFICATION"
      ? "gold"
      : "red";

  // Extract ratio results from API response
  const ratios = result?.quantitative_screen
    ? Object.entries(result.quantitative_screen)
        .filter(([key, val]) => typeof val === "object" && val !== null && "value" in val)
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
            {/* Stock header */}
            <div className="p-6 border-b border-gray-100">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <h3 className="text-2xl font-bold text-mizan-ink font-arabic">
                    {locale === "ar" ? result.name_ar || result.company : result.company}
                  </h3>
                  <p className="text-sm text-mizan-slate mt-1 font-arabic">
                    {locale === "ar" ? result.sector_ar || result.sector : result.sector}
                    {result.ticker && <span className="ml-2 text-gray-400">#{result.ticker}</span>}
                  </p>
                </div>
                {/* Verdict badge */}
                <div
                  className={`px-5 py-3 rounded-xl font-bold text-sm flex items-center gap-2 font-arabic ${
                    verdictColor === "green"
                      ? "bg-green-50 text-green-700 border border-green-200"
                      : verdictColor === "gold"
                      ? "bg-amber-50 text-amber-700 border border-amber-200"
                      : "bg-red-50 text-red-700 border border-red-200"
                  }`}
                >
                  <span className="text-xl">
                    {verdictColor === "green" ? "✅" : verdictColor === "gold" ? "✅⚠️" : "❌"}
                  </span>
                  {locale === "ar" ? result.verdict_ar : result.verdict.replace(/_/g, " ")}
                </div>
              </div>
            </div>

            {/* Ratios */}
            {ratios.length > 0 && (
              <div className="p-6 border-b border-gray-100">
                <h4 className="text-sm font-semibold text-mizan-ink mb-4 font-arabic">
                  {locale === "ar" ? "المؤشرات المالية (معيار AAOIFI 21)" : "Financial Ratios (AAOIFI Standard 21)"}
                </h4>
                <div className="space-y-3">
                  {ratios.map((ratio, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm text-mizan-slate font-arabic">{ratio.label}</span>
                      <div className="flex items-center gap-3">
                        <span className={`text-sm font-mono ${ratio.pass ? "text-green-600" : "text-red-600"}`}>
                          {ratio.value}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded ${ratio.pass ? "bg-green-50 text-green-600" : "bg-red-50 text-red-600"}`}>
                          {ratio.pass
                            ? (locale === "ar" ? "مقبول" : "Pass")
                            : (locale === "ar" ? "مرفوض" : "Fail")}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Detail */}
            <div className="p-6 bg-gray-50/50">
              <p className="text-sm text-mizan-slate font-arabic leading-relaxed">
                {result.verdict_detail}
              </p>
              <p className="text-xs text-gray-400 mt-3 font-arabic">
                {locale === "ar" ? "المعيار: معيار الأوراق المالية الإسلامية رقم 21" : "Standard: AAOIFI Securities Standard No. 21"}
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

// Helper: human-readable ratio labels
function ratioLabel(key: string, locale: string): string {
  const labels: Record<string, { ar: string; en: string }> = {
    debt_to_assets: { ar: "الدين / إجمالي الأصول", en: "Debt / Assets" },
    debt_to_market_cap: { ar: "الدين / القيمة السوقية", en: "Debt / Market Cap" },
    interest_bearing_investments_to_assets: { ar: "استثمات بفائدة / الأصول", en: "Interest Investments / Assets" },
    interest_bearing_investments_to_market_cap: { ar: "استثمات بفائدة / القيمة السوقية", en: "Interest Investments / Market Cap" },
    receivables_to_total: { ar: "المستحقات / الإجمالي", en: "Receivables / Total" },
    non_compliant_income: { ar: "الدخل غير المشروع", en: "Non-compliant Income" },
  };
  const l = labels[key];
  if (!l) return key;
  return locale === "ar" ? l.ar : l.en;
}
