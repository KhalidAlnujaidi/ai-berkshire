"use client";

import { useState, useEffect, useRef } from "react";
import type { Dict } from "@/i18n/ar";

interface PortfolioScreenerProps {
  dict: Dict;
  locale: string;
}

interface StockEntry {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
}

interface Holding {
  ticker: string;
  amount: string;
}

interface PortfolioHoldingResult {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
  amount: number;
  currency: string;
  verdict: string;
  verdict_ar: string;
  verdict_detail: string;
  is_halal: boolean;
  needs_purification: boolean;
  weight_pct: number;
}

interface PortfolioSummary {
  total_holdings: number;
  total_amount: number;
  halal_amount: number;
  halal_pct: number;
  non_compliant_amount: number;
  non_compliant_pct: number;
  purification_amount: number;
  purification_pct: number;
  grade: string;
  grade_ar: string;
}

interface Recommendation {
  type: string;
  title_en: string;
  title_ar: string;
  detail_en: string;
  detail_ar: string;
  severity: string;
}

interface PortfolioResult {
  holdings: PortfolioHoldingResult[];
  summary: PortfolioSummary;
  recommendations: Recommendation[];
  not_found: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function verdictBadge(v: string) {
  if (v === "COMPLIANT") return { color: "bg-mizan-green", text: "\u2713" };
  if (v === "COMPLIANT_WITH_OVERLAY" || v === "COMPLIANT_WITH_PURIFICATION")
    return { color: "bg-mizan-gold", text: "\u26a0" };
  return { color: "bg-red-500", text: "\u2717" };
}

function gradeColor(grade: string) {
  switch (grade) {
    case "SHARIA_COMPLIANT":
      return "from-mizan-green to-mizan-green-dark";
    case "PURIFICATION_REQUIRED":
      return "from-mizan-gold to-amber-600";
    case "NEEDS_REBALANCING":
      return "from-orange-500 to-orange-600";
    case "HIGH_RISK":
      return "from-red-500 to-red-600";
    default:
      return "from-gray-500 to-gray-600";
  }
}

function severityStyle(severity: string) {
  switch (severity) {
    case "critical":
      return { border: "border-red-300 bg-red-50", icon: "\uD83D\uDEAB" };
    case "warning":
      return { border: "border-amber-300 bg-amber-50", icon: "\u26a0\ufe0f" };
    case "success":
      return { border: "border-mizan-green/30 bg-mizan-green-pale", icon: "\u2705" };
    default:
      return { border: "border-gray-200 bg-gray-50", icon: "\u2139\ufe0f" };
  }
}

function fmtNum(n: number, locale: string) {
  return n.toLocaleString(locale === "ar" ? "ar-SA" : "en-US", { maximumFractionDigits: 0 });
}

export default function PortfolioScreener({ dict, locale }: PortfolioScreenerProps) {
  const p = dict.portfolio;
  const [allStocks, setAllStocks] = useState<StockEntry[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([{ ticker: "", amount: "" }]);
  const [result, setResult] = useState<PortfolioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchIndex, setSearchIndex] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function fetchStocks() {
      try {
        const res = await fetch(`${API_BASE}/api/stocks`);
        if (res.ok) setAllStocks(await res.json());
      } catch {
        setAllStocks([
          { ticker: "1120", name_en: "Al Rajhi Bank", name_ar: "\u0645\u0635\u0631\u0641 \u0627\u0644\u0631\u0627\u062c\u062d\u064a", sector_en: "Islamic Banking", sector_ar: "\u0645\u0635\u0631\u0641\u064a \u0625\u0633\u0644\u0627\u0645\u064a" },
          { ticker: "2222", name_en: "Saudi Aramco", name_ar: "\u0623\u0631\u0627\u0645\u0643\u0648 \u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629", sector_en: "Energy", sector_ar: "\u0627\u0644\u0637\u0627\u0642\u0629" },
          { ticker: "7010", name_en: "STC Group", name_ar: "\u0645\u062c\u0645\u0648\u0639\u0629 \u0625\u0633 \u062a\u064a \u0633\u064a", sector_en: "Telecommunications", sector_ar: "\u0627\u0644\u0627\u062a\u0635\u0627\u0644\u0627\u062a" },
          { ticker: "2010", name_en: "SABIC", name_ar: "\u0633\u0627\u0628\u0643", sector_en: "Petrochemicals", sector_ar: "\u0627\u0644\u0628\u062a\u0631\u0648\u0643\u064a\u0645\u0627\u0648\u064a\u0627\u062a" },
          { ticker: "1180", name_en: "Saudi National Bank", name_ar: "\u0628\u0646\u0643 \u0627\u0644\u0623\u0647\u0644\u064a", sector_en: "Conventional Banking", sector_ar: "\u0645\u0635\u0631\u0641\u064a \u062a\u0642\u0644\u064a\u062f\u064a" },
          { ticker: "2380", name_en: "Bank Albilad", name_ar: "\u0628\u0646\u0643 \u0627\u0644\u0628\u0644\u0627\u062f", sector_en: "Islamic Banking", sector_ar: "\u0645\u0635\u0631\u0641\u064a \u0625\u0633\u0644\u0627\u0645\u064a" },
        ]);
      }
    }
    fetchStocks();
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function updateHolding(idx: number, field: keyof Holding, value: string) {
    const updated = [...holdings];
    updated[idx] = { ...updated[idx], [field]: value };
    setHoldings(updated);
  }

  function addHolding() {
    setHoldings([...holdings, { ticker: "", amount: "" }]);
  }

  function removeHolding(idx: number) {
    if (holdings.length === 1) return;
    setHoldings(holdings.filter((_, i) => i !== idx));
  }

  function pickStock(ticker: string) {
    if (searchIndex !== null) {
      updateHolding(searchIndex, "ticker", ticker);
    }
    setSearch("");
    setShowDropdown(false);
    setSearchIndex(null);
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

  async function analyze() {
    const valid = holdings.filter((h) => h.ticker.trim() && parseFloat(h.amount) > 0);
    if (valid.length === 0) {
      setError(p.empty);
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/portfolio-screen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          holdings: valid.map((h) => ({
            ticker: h.ticker.trim(),
            amount: parseFloat(h.amount),
          })),
        }),
      });
      if (res.ok) {
        setResult(await res.json());
      } else {
        setError(locale === "ar" ? "\u062d\u062f\u062b \u062e\u0637\u0623. \u062d\u0627\u0648\u0644 \u0645\u0631\u0629 \u0623\u062e\u0631\u0649." : "An error occurred. Try again.");
      }
    } catch {
      setError(locale === "ar" ? "\u062a\u0639\u0630\u0631 \u0627\u0644\u0627\u062a\u0635\u0627\u0644 \u0628\u0627\u0644\u062e\u0627\u062f\u0645." : "Could not connect to server.");
    } finally {
      setLoading(false);
    }
  }

  function loadExample() {
    setHoldings([
      { ticker: "1120", amount: "50000" },
      { ticker: "2222", amount: "30000" },
      { ticker: "1180", amount: "20000" },
    ]);
  }

  const summary = result?.summary;

  return (
    <section id="portfolio" className="py-20 md:py-28 bg-gradient-to-b from-mizan-green-pale/20 to-white">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-mizan-green/10 rounded-full mb-4">
            <span className="text-sm font-medium text-mizan-green-dark font-arabic">
              {locale === "ar" ? "\u0623\u062f\u0627\u0629 \u0641\u062d\u0635 \u0627\u0644\u0645\u062d\u0641\u0638\u0629" : "Portfolio Screening Tool"}
            </span>
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-4 font-arabic">
            {p.title}
          </h2>
          <p className="text-lg text-mizan-slate font-arabic max-w-2xl mx-auto">
            {p.subtitle}
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 md:p-8 mb-8">
          <div className="space-y-4" ref={dropdownRef}>
            {holdings.map((holding, idx) => (
              <div key={idx} className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
                <div className="flex-1 w-full relative">
                  <input
                    type="text"
                    value={idx === searchIndex ? search : holding.ticker}
                    onChange={(e) => {
                      setSearchIndex(idx);
                      setSearch(e.target.value);
                      updateHolding(idx, "ticker", e.target.value);
                      setShowDropdown(true);
                    }}
                    onFocus={() => {
                      setSearchIndex(idx);
                      setSearch(holding.ticker);
                      setShowDropdown(true);
                    }}
                    placeholder={p.tickerPlaceholder}
                    className="w-full px-4 py-3 text-base rounded-xl border-2 border-gray-200 focus:border-mizan-green focus:ring-0 focus:outline-none transition-colors font-arabic"
                    dir={locale === "ar" ? "rtl" : "ltr"}
                  />
                  {showDropdown && searchIndex === idx && (
                    <div className="absolute z-20 mt-1 w-full bg-white rounded-xl shadow-2xl border border-gray-100 max-h-60 overflow-y-auto">
                      {filtered.slice(0, 8).map((s) => (
                        <button
                          key={s.ticker}
                          onClick={() => pickStock(s.ticker)}
                          className="w-full text-left px-4 py-2.5 hover:bg-mizan-green-pale transition-colors flex items-center gap-3"
                        >
                          <span className="font-mono font-bold text-mizan-green text-sm min-w-[3rem]">{s.ticker}</span>
                          <span className="text-sm text-mizan-ink font-arabic">
                            {locale === "ar" ? s.name_ar : s.name_en}
                          </span>
                        </button>
                      ))}
                      {filtered.length === 0 && (
                        <div className="px-4 py-3 text-sm text-mizan-slate font-arabic">
                          {locale === "ar" ? "\u0644\u0627 \u0646\u062a\u0627\u0626\u062c" : "No results"}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <input
                  type="number"
                  value={holding.amount}
                  onChange={(e) => updateHolding(idx, "amount", e.target.value)}
                  placeholder={p.amountPlaceholder}
                  className="w-full sm:w-40 px-4 py-3 text-base rounded-xl border-2 border-gray-200 focus:border-mizan-green focus:ring-0 focus:outline-none transition-colors font-arabic"
                  dir="ltr"
                />
                {holdings.length > 1 && (
                  <button
                    onClick={() => removeHolding(idx)}
                    className="p-3 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                    title={p.remove}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-3 mt-6">
            <button onClick={addHolding} className="px-5 py-2.5 text-sm font-semibold text-mizan-green bg-mizan-green-pale hover:bg-mizan-green/20 rounded-xl transition-colors font-arabic">
              + {p.addHolding}
            </button>
            <button onClick={loadExample} className="px-5 py-2.5 text-sm font-medium text-mizan-slate hover:text-mizan-green transition-colors font-arabic">
              {p.addExample}
            </button>
            <button onClick={analyze} disabled={loading} className="ml-auto px-8 py-3 text-sm font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-arabic">
              {loading ? p.analyzing : p.analyze}
            </button>
          </div>
          {error && <p className="mt-4 text-sm text-red-500 font-arabic text-center">{error}</p>}
        </div>

        {summary && result && (
          <div className="space-y-6 animate-fade-in">
            <div className={`bg-gradient-to-br ${gradeColor(summary.grade)} rounded-2xl p-8 shadow-xl`}>
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="text-center md:text-right">
                  <p className="text-sm text-white/80 font-arabic mb-1">{locale === "ar" ? summary.grade_ar : summary.grade.replace(/_/g, " ")}</p>
                  <p className="text-5xl md:text-6xl font-bold text-white font-arabic">
                    {summary.halal_pct.toFixed(1)}<span className="text-3xl">%</span>
                  </p>
                  <p className="text-sm text-white/80 font-arabic mt-1">{p.halalScore}</p>
                </div>
                <div className="grid grid-cols-2 gap-4 w-full md:w-auto">
                  <div className="bg-white/15 backdrop-blur-sm rounded-xl p-4 text-center">
                    <p className="text-xs text-white/70 font-arabic mb-1">{p.totalValue}</p>
                    <p className="text-lg font-bold text-white font-arabic">{fmtNum(summary.total_amount, locale)}</p>
                  </div>
                  <div className="bg-white/15 backdrop-blur-sm rounded-xl p-4 text-center">
                    <p className="text-xs text-white/70 font-arabic mb-1">{p.holdings}</p>
                    <p className="text-lg font-bold text-white font-arabic">{summary.total_holdings}</p>
                  </div>
                  <div className="bg-white/15 backdrop-blur-sm rounded-xl p-4 text-center">
                    <p className="text-xs text-white/70 font-arabic mb-1">{p.halalAmount}</p>
                    <p className="text-lg font-bold text-white font-arabic">{summary.halal_pct.toFixed(0)}%</p>
                  </div>
                  <div className="bg-white/15 backdrop-blur-sm rounded-xl p-4 text-center">
                    <p className="text-xs text-white/70 font-arabic mb-1">{p.nonCompliantAmount}</p>
                    <p className="text-lg font-bold text-white font-arabic">{summary.non_compliant_pct.toFixed(0)}%</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
              <div className="h-6 rounded-full overflow-hidden flex">
                <div className="bg-mizan-green h-full flex items-center justify-center text-xs text-white font-bold transition-all duration-500" style={{ width: `${summary.halal_pct - summary.purification_pct}%` }}>
                  {summary.halal_pct - summary.purification_pct > 10 ? "\u2713" : ""}
                </div>
                <div className="bg-mizan-gold h-full flex items-center justify-center text-xs text-white font-bold transition-all duration-500" style={{ width: `${summary.purification_pct}%` }}>
                  {summary.purification_pct > 10 ? "\u26a0" : ""}
                </div>
                <div className="bg-red-500 h-full flex items-center justify-center text-xs text-white font-bold transition-all duration-500" style={{ width: `${summary.non_compliant_pct}%` }}>
                  {summary.non_compliant_pct > 10 ? "\u2717" : ""}
                </div>
              </div>
              <div className="flex gap-4 mt-3 text-xs font-arabic">
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-mizan-green inline-block"></span> {p.halalAmount} ({(summary.halal_pct - summary.purification_pct).toFixed(1)}%)</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-mizan-gold inline-block"></span> {p.purificationAmount} ({summary.purification_pct.toFixed(1)}%)</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> {p.nonCompliantAmount} ({summary.non_compliant_pct.toFixed(1)}%)</span>
              </div>
            </div>

            {result.recommendations.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                <h3 className="text-lg font-bold text-mizan-ink mb-4 font-arabic">{p.recommendations}</h3>
                <div className="space-y-3">
                  {result.recommendations.map((rec, i) => {
                    const st = severityStyle(rec.severity);
                    return (
                      <div key={i} className={`border ${st.border} rounded-xl p-4 flex items-start gap-3`}>
                        <span className="text-xl flex-shrink-0">{st.icon}</span>
                        <div>
                          <p className="font-semibold text-mizan-ink font-arabic text-sm">
                            {locale === "ar" ? rec.title_ar : rec.title_en}
                          </p>
                          <p className="text-sm text-mizan-slate mt-1 font-arabic">
                            {locale === "ar" ? rec.detail_ar : rec.detail_en}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-lg font-bold text-mizan-ink font-arabic">{p.perHolding}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-mizan-slate uppercase tracking-wide font-arabic">{locale === "ar" ? "\u0627\u0644\u0633\u0647\u0645" : "Stock"}</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-mizan-slate uppercase tracking-wide font-arabic">{p.sector}</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-mizan-slate uppercase tracking-wide font-arabic">{p.amount}</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-mizan-slate uppercase tracking-wide font-arabic">{p.weight}</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-mizan-slate uppercase tracking-wide font-arabic">{p.verdict}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {result.holdings.map((h) => {
                      const badge = verdictBadge(h.verdict);
                      return (
                        <tr key={h.ticker} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-bold text-mizan-green text-sm">{h.ticker}</span>
                              <span className="text-sm text-mizan-ink font-arabic">
                                {locale === "ar" ? h.name_ar : h.name_en}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-mizan-slate font-arabic">
                            {locale === "ar" ? h.sector_ar : h.sector_en}
                          </td>
                          <td className="px-4 py-3 text-sm font-semibold text-mizan-ink font-arabic" dir="ltr">
                            {fmtNum(h.amount, locale)} {h.currency}
                          </td>
                          <td className="px-4 py-3 text-sm text-mizan-slate font-arabic">
                            {h.weight_pct.toFixed(1)}%
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full ${badge.color} text-white text-sm font-bold`}>
                              {badge.text}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
