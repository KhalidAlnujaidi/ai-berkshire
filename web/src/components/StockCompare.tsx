"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";

interface StockCompareProps {
  dict: Dict;
  locale: string;
}

// ── Types ──────────────────────────────────────────────────────────────────

interface RatioResult {
  value: number;
  threshold: string;
  passed: boolean;
}

interface StockEntry {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
}

interface StockDetail {
  company: string;
  ticker: string;
  sector: string;
  name_ar: string;
  sector_ar: string;
  verdict: string;
  verdict_ar: string;
  verdict_detail: string;
  qualitative_screen: { compliant: boolean; category: string; notes: string };
  quantitative_screen: Record<string, RatioResult | boolean> | null;
  market: string;
  currency: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Verdict helpers ────────────────────────────────────────────────────────

function verdictRank(v: string): number {
  if (v === "COMPLIANT") return 3;
  if (v === "COMPLIANT_WITH_OVERLAY" || v === "COMPLIANT_WITH_PURIFICATION") return 2;
  return 0;
}

function verdictBadge(v: string, locale: string) {
  if (v === "COMPLIANT")
    return { color: "bg-mizan-green", text: locale === "ar" ? "متوافق" : "Compliant", icon: "✓" };
  if (v === "COMPLIANT_WITH_OVERLAY" || v === "COMPLIANT_WITH_PURIFICATION")
    return { color: "bg-mizan-gold", text: locale === "ar" ? "يتطلب تنقية" : "Purification", icon: "⚠" };
  return { color: "bg-red-500", text: locale === "ar" ? "غير متوافق" : "Non-compliant", icon: "✗" };
}

const RATIO_KEYS = [
  "debt_to_assets",
  "debt_to_market_cap",
  "interest_bearing_investments_to_assets",
  "interest_bearing_investments_to_market_cap",
  "receivables_to_total",
  "non_compliant_income",
];

function ratioLabel(key: string, dict: Dict) {
  const map: Record<string, string> = {
    debt_to_assets: dict.compare.metricDebtAssets,
    debt_to_market_cap: dict.compare.metricDebtMcap,
    interest_bearing_investments_to_assets: dict.compare.metricInterestInv,
    interest_bearing_investments_to_market_cap: dict.compare.metricInterestInv,
    receivables_to_total: dict.compare.metricReceivables,
    non_compliant_income: dict.compare.metricNonCompliant,
  };
  return map[key] || key;
}

// ── Component ──────────────────────────────────────────────────────────────

export default function StockCompare({ dict, locale }: StockCompareProps) {
  const c = dict.compare;
  const [allStocks, setAllStocks] = useState<StockEntry[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [details, setDetails] = useState<Record<string, StockDetail>>({});
  const [loadingStocks, setLoadingStocks] = useState<Record<string, boolean>>({});
  const [search, setSearch] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch all stocks for the picker
  useEffect(() => {
    async function fetchStocks() {
      try {
        const res = await fetch(`${API_BASE}/api/stocks`);
        if (res.ok) setAllStocks(await res.json());
      } catch {
        // Fallback
        setAllStocks([
          { ticker: "1120", name_en: "Al Rajhi Bank", name_ar: "مصرف الراجحي", sector_en: "Islamic Banking", sector_ar: "الخدمات المصرفية الإسلامية" },
          { ticker: "2222", name_en: "Saudi Aramco", name_ar: "أرامكو السعودية", sector_en: "Energy", sector_ar: "الطاقة" },
          { ticker: "7010", name_en: "STC Group", name_ar: "مجموعة إس تي سي", sector_en: "Telecommunications", sector_ar: "الاتصالات" },
          { ticker: "2010", name_en: "SABIC", name_ar: "سابك", sector_en: "Petrochemicals", sector_ar: "البتروكيماويات" },
          { ticker: "1180", name_en: "Saudi National Bank", name_ar: "بنك الأهلي", sector_en: "Conventional Banking", sector_ar: "مصرفي تقليدي" },
          { ticker: "2380", name_en: "Bank Albilad", name_ar: "بنك البلاد", sector_en: "Islamic Banking", sector_ar: "مصرفي إسلامي" },
        ]);
      }
    }
    fetchStocks();
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Fetch detail when a stock is selected
  useEffect(() => {
    for (const ticker of selected) {
      if (!details[ticker] && !loadingStocks[ticker]) {
        setLoadingStocks((s) => ({ ...s, [ticker]: true }));
        fetch(`${API_BASE}/api/stocks/${encodeURIComponent(ticker)}`)
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data) setDetails((d) => ({ ...d, [ticker]: data }));
          })
          .catch(() => {})
          .finally(() => setLoadingStocks((s) => ({ ...s, [ticker]: false })));
      }
    }
  }, [selected]); // eslint-disable-line react-hooks/exhaustive-deps

  function addStock(ticker: string) {
    if (selected.length >= 3 || selected.includes(ticker)) return;
    setSelected([...selected, ticker]);
    setSearch("");
    setShowDropdown(false);
  }

  function removeStock(ticker: string) {
    setSelected(selected.filter((t) => t !== ticker));
  }

  const filtered = allStocks.filter((s) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return (
      s.ticker.includes(q) ||
      s.name_en.toLowerCase().includes(q) ||
      s.name_ar.includes(search.trim())
    );
  });

  // Determine best-in-class for each ratio (lowest value wins for debt/interest ratios)
  function bestTickerForRatio(ratioKey: string): string | null {
    let best: string | null = null;
    let bestVal = Infinity;
    for (const ticker of selected) {
      const detail = details[ticker];
      if (!detail?.quantitative_screen) continue;
      const entry = detail.quantitative_screen[ratioKey];
      if (entry && typeof entry === "object" && "value" in entry) {
        if ((entry as RatioResult).value < bestVal) {
          bestVal = (entry as RatioResult).value;
          best = ticker;
        }
      }
    }
    return best;
  }

  return (
    <section id="compare" className="py-20 md:py-28 bg-gradient-to-b from-white to-mizan-green-pale/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-mizan-gold/10 rounded-full mb-4">
            <span className="text-sm font-medium text-mizan-gold-dark font-arabic">
              {locale === "ar" ? "أداة المقارنة" : "Comparison Tool"}
            </span>
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-4 font-arabic">
            {c.title}
          </h2>
          <p className="text-lg text-mizan-slate font-arabic max-w-2xl mx-auto">
            {c.subtitle}
          </p>
        </div>

        {/* Stock picker */}
        <div className="max-w-2xl mx-auto mb-8" ref={dropdownRef}>
          <div className="relative">
            <div className="flex gap-2">
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setShowDropdown(true);
                }}
                onFocus={() => setShowDropdown(true)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && filtered.length > 0) {
                    addStock(filtered[0].ticker);
                  }
                }}
                placeholder={c.searchPlaceholder}
                disabled={selected.length >= 3}
                className="flex-1 px-5 py-3.5 text-base rounded-xl border-2 border-gray-200 focus:border-mizan-green focus:ring-0 focus:outline-none transition-colors font-arabic disabled:opacity-50"
                dir={locale === "ar" ? "rtl" : "ltr"}
              />
              <button
                onClick={() => {
                  if (filtered.length > 0) addStock(filtered[0].ticker);
                }}
                disabled={selected.length >= 3 || filtered.length === 0}
                className="px-6 py-3.5 text-sm font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-arabic whitespace-nowrap"
              >
                {c.addStock}
              </button>
            </div>

            {/* Dropdown */}
            {showDropdown && selected.length < 3 && (
              <div className="absolute z-20 mt-1 w-full bg-white rounded-xl shadow-xl border border-gray-100 max-h-64 overflow-y-auto">
                {filtered.length === 0 ? (
                  <div className="px-4 py-3 text-sm text-mizan-slate font-arabic">
                    {locale === "ar" ? "لا توجد نتائج" : "No results"}
                  </div>
                ) : (
                  filtered.slice(0, 20).map((s) => (
                    <button
                      key={s.ticker}
                      onClick={() => addStock(s.ticker)}
                      disabled={selected.includes(s.ticker)}
                      className="w-full text-left px-4 py-3 hover:bg-mizan-green-pale transition-colors flex items-center justify-between gap-3 disabled:opacity-30 border-b border-gray-50 last:border-0"
                    >
                      <div>
                        <span className="font-medium text-mizan-ink font-arabic">
                          {locale === "ar" ? s.name_ar : s.name_en}
                        </span>
                        <span className="text-xs text-mizan-slate ml-2">({s.ticker})</span>
                      </div>
                      <span className="text-xs text-mizan-slate font-arabic">
                        {locale === "ar" ? s.sector_ar : s.sector_en}
                      </span>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
          {selected.length >= 3 && (
            <p className="text-sm text-mizan-gold mt-2 text-center font-arabic">{c.maxReached}</p>
          )}
        </div>

        {/* Empty state */}
        {selected.length === 0 && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">📊</div>
            <p className="text-lg text-mizan-slate font-arabic">{c.pickPrompt}</p>
          </div>
        )}

        {/* Comparison table */}
        {selected.length > 0 && (
          <div className="overflow-x-auto rounded-2xl shadow-lg border border-gray-100">
            <table className="w-full">
              {/* Column headers — stock names */}
              <thead>
                <tr className="bg-white border-b border-gray-100">
                  <th className="sticky left-0 bg-white px-4 py-4 text-left text-xs font-medium text-mizan-slate uppercase tracking-wider font-arabic min-w-[140px]">
                    {locale === "ar" ? "المقياس" : "Metric"}
                  </th>
                  {selected.map((ticker) => {
                    const stock = allStocks.find((s) => s.ticker === ticker);
                    return (
                      <th key={ticker} className="px-4 py-4 text-center min-w-[180px]">
                        <div className="flex flex-col items-center gap-1">
                          <Link
                            href={`/${locale}/stock/${ticker}`}
                            className="font-bold text-mizan-ink hover:text-mizan-green transition-colors font-arabic"
                          >
                            {locale === "ar" ? stock?.name_ar || ticker : stock?.name_en || ticker}
                          </Link>
                          <span className="text-xs font-mono text-mizan-slate bg-gray-100 px-2 py-0.5 rounded">
                            {ticker}
                          </span>
                          <button
                            onClick={() => removeStock(ticker)}
                            className="text-xs text-red-400 hover:text-red-600 font-arabic mt-1"
                          >
                            ✕ {c.remove}
                          </button>
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>

              <tbody className="bg-white">
                {/* Verdict row */}
                <CompareRow label={c.metricVerdict} dict={dict}>
                  {selected.map((ticker) => {
                    const d = details[ticker];
                    const loading = loadingStocks[ticker];
                    if (loading) return <td key={ticker} className="px-4 py-3 text-center"><Spinner /></td>;
                    if (!d) return <td key={ticker} className="px-4 py-3 text-center text-mizan-slate text-sm">—</td>;
                    const badge = verdictBadge(d.verdict, locale);
                    return (
                      <td key={ticker} className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold text-white ${badge.color}`}>
                          {badge.icon} {badge.text}
                        </span>
                      </td>
                    );
                  })}
                </CompareRow>

                {/* Sector row */}
                <CompareRow label={c.metricSector} dict={dict}>
                  {selected.map((ticker) => {
                    const d = details[ticker];
                    return (
                      <td key={ticker} className="px-4 py-3 text-center text-sm text-mizan-slate font-arabic">
                        {d ? (locale === "ar" ? d.sector_ar : d.sector) : "—"}
                      </td>
                    );
                  })}
                </CompareRow>

                {/* Market row */}
                <CompareRow label={c.metricMarket} dict={dict}>
                  {selected.map((ticker) => {
                    const d = details[ticker];
                    return (
                      <td key={ticker} className="px-4 py-3 text-center text-sm text-mizan-slate">
                        {d ? `${d.market} (${d.currency})` : "—"}
                      </td>
                    );
                  })}
                </CompareRow>

                {/* Ratio rows */}
                {RATIO_KEYS.map((ratioKey) => {
                  const bestTicker = bestTickerForRatio(ratioKey);
                  return (
                    <CompareRow key={ratioKey} label={ratioLabel(ratioKey, dict)} dict={dict}>
                      {selected.map((ticker) => {
                        const d = details[ticker];
                        if (!d?.quantitative_screen) {
                          return <td key={ticker} className="px-4 py-3 text-center text-mizan-slate text-sm">—</td>;
                        }
                        const entry = d.quantitative_screen[ratioKey];
                        if (!entry || typeof entry !== "object" || !("value" in entry)) {
                          return <td key={ticker} className="px-4 py-3 text-center text-mizan-slate text-sm">—</td>;
                        }
                        const r = entry as RatioResult;
                        const isBest = ticker === bestTicker && selected.length > 1;
                        return (
                          <td key={ticker} className="px-4 py-3 text-center">
                            <div className="inline-flex flex-col items-center gap-1">
                              <span className={`font-mono text-sm font-medium ${r.passed ? "text-mizan-green" : "text-red-500"}`}>
                                {r.value.toFixed(2)}%
                              </span>
                              <span className="text-[10px] text-mizan-slate">≤ {r.threshold}</span>
                              {isBest && (
                                <span className="text-[10px] bg-mizan-gold/15 text-mizan-gold-dark px-2 py-0.5 rounded-full font-medium font-arabic">
                                  {c.bestInClass}
                                </span>
                              )}
                              <span className={r.passed ? "text-mizan-green text-xs" : "text-red-500 text-xs"}>
                                {r.passed ? "✓" : "✗"}
                              </span>
                            </div>
                          </td>
                        );
                      })}
                    </CompareRow>
                  );
                })}

                {/* Pass count summary row */}
                <CompareRow label={c.passCount} dict={dict} highlight>
                  {selected.map((ticker) => {
                    const d = details[ticker];
                    if (!d?.quantitative_screen) {
                      return <td key={ticker} className="px-4 py-3 text-center text-mizan-slate text-sm">—</td>;
                    }
                    const ratios = Object.values(d.quantitative_screen).filter(
                      (v): v is RatioResult => typeof v === "object" && v !== null && "passed" in v
                    );
                    const passCount = ratios.filter((r) => r.passed).length;
                    const total = ratios.length;
                    return (
                      <td key={ticker} className="px-4 py-3 text-center">
                        <span className="text-lg font-bold text-mizan-green">
                          {passCount}
                          <span className="text-sm text-mizan-slate">/{total}</span>
                        </span>
                      </td>
                    );
                  })}
                </CompareRow>
              </tbody>
            </table>
          </div>
        )}

        {/* Link back to discover */}
        {selected.length > 0 && (
          <div className="text-center mt-8">
            <Link
              href={`/${locale}#discover`}
              className="text-sm text-mizan-green hover:underline font-arabic"
            >
              {locale === "ar" ? "← العودة للأسهم الحلال" : "← Back to Halal Stocks"}
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function CompareRow({
  label,
  children,
  dict,
  highlight,
}: {
  label: string;
  children: React.ReactNode;
  dict: Dict;
  highlight?: boolean;
}) {
  return (
    <tr className={`border-b border-gray-50 ${highlight ? "bg-mizan-green-pale/30" : ""}`}>
      <td className={`sticky left-0 ${highlight ? "bg-mizan-green-pale/30" : "bg-white"} px-4 py-3 text-xs font-medium text-mizan-slate uppercase tracking-wider font-arabic whitespace-nowrap`}>
        {label}
      </td>
      {children}
    </tr>
  );
}

function Spinner() {
  return (
    <div className="inline-block w-4 h-4 border-2 border-mizan-green border-t-transparent rounded-full animate-spin" />
  );
}
