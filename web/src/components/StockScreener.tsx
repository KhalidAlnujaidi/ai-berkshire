"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";
import type { Locale } from "@/i18n";

interface ScreenerProps {
  dict: Dict;
  locale: Locale;
}

interface ScreenerStock {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
  market_cap: number;
  currency: string;
  verdict: string;
  verdict_ar: string;
  is_halal: boolean;
  ratios: {
    debt_to_assets: number | null;
    debt_to_market_cap: number | null;
    interest_investments_ratio: number | null;
    receivables_ratio: number | null;
    non_compliant_income_ratio: number | null;
    illiquid_assets_ratio: number | null;
  };
}

interface Sector {
  sector_en: string;
  sector_ar: string;
  count: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function formatMarketCap(value: number, locale: Locale): string {
  if (!value) return "—";
  const billions = value / 1_000_000_000;
  if (billions >= 1000) return `${(billions / 1000).toFixed(1)}T`;
  if (billions >= 1) return `${billions.toFixed(1)}B`;
  return `${(value / 1_000_000).toFixed(0)}M`;
}

function verdictBadge(verdict: string, is_halal: boolean) {
  if (verdict === "COMPLIANT") {
    return { bg: "bg-emerald-500/15", text: "text-emerald-400", border: "border-emerald-500/30", icon: "✓" };
  } else if (verdict === "COMPLIANT_WITH_PURIFICATION" || verdict === "COMPLIANT_WITH_OVERLAY") {
    return { bg: "bg-amber-500/15", text: "text-amber-400", border: "border-amber-500/30", icon: "⚠" };
  } else {
    return { bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30", icon: "✗" };
  }
}

export default function StockScreener({ dict, locale }: ScreenerProps) {
  const s = dict.screener;
  const [stocks, setStocks] = useState<ScreenerStock[]>([]);
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalUniverse, setTotalUniverse] = useState(0);

  // Filters
  const [compliance, setCompliance] = useState("");
  const [sector, setSector] = useState("");
  const [maxDebtRatio, setMaxDebtRatio] = useState("");
  const [maxNcIncome, setMaxNcIncome] = useState("");
  const [minMarketCap, setMinMarketCap] = useState("");
  const [sortBy, setSortBy] = useState("ticker");
  const [sortOrder, setSortOrder] = useState("asc");

  const fetchSectors = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sectors`);
      if (res.ok) {
        setSectors(await res.json());
      }
    } catch {
      // fallback empty
    }
  }, []);

  const fetchScreened = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (compliance) params.set("compliance", compliance);
      if (sector) params.set("sector", sector);
      if (maxDebtRatio) params.set("max_debt_ratio", maxDebtRatio);
      if (maxNcIncome) params.set("max_non_compliant_income", maxNcIncome);
      if (minMarketCap) params.set("min_market_cap", String(parseFloat(minMarketCap) * 1_000_000_000));
      if (sortBy) params.set("sort_by", sortBy);
      if (sortOrder) params.set("sort_order", sortOrder);

      const res = await fetch(`${API_BASE}/api/screen?${params}`);
      if (res.ok) {
        const data = await res.json();
        setStocks(data.stocks);
        setTotalUniverse(data.total_universe);
      } else {
        setStocks([]);
      }
    } catch {
      setStocks([]);
    } finally {
      setLoading(false);
    }
  }, [compliance, sector, maxDebtRatio, maxNcIncome, minMarketCap, sortBy, sortOrder]);

  useEffect(() => {
    fetchSectors();
  }, [fetchSectors]);

  useEffect(() => {
    fetchScreened();
  }, [fetchScreened]);

  const reset = () => {
    setCompliance("");
    setSector("");
    setMaxDebtRatio("");
    setMaxNcIncome("");
    setMinMarketCap("");
    setSortBy("ticker");
    setSortOrder("asc");
  };

  return (
    <section id="screener" className="py-20 bg-gradient-to-b from-gray-950 to-gray-900 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-3">{s.title}</h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">{s.subtitle}</p>
        </div>

        {/* Filter Bar */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6 mb-8 backdrop-blur-sm">
          <h3 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider text-emerald-400">{s.filtersTitle}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Compliance */}
            <div>
              <label className="block text-gray-400 text-sm mb-1.5">{s.complianceLabel}</label>
              <select
                value={compliance}
                onChange={(e) => setCompliance(e.target.value)}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none transition"
              >
                <option value="">{s.complianceOptions.all}</option>
                <option value="compliant">{s.complianceOptions.compliant}</option>
                <option value="purification">{s.complianceOptions.purification}</option>
                <option value="non_compliant">{s.complianceOptions.non_compliant}</option>
                <option value="all_halal">{s.complianceOptions.all_halal}</option>
              </select>
            </div>

            {/* Sector */}
            <div>
              <label className="block text-gray-400 text-sm mb-1.5">{s.sectorLabel}</label>
              <select
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none transition"
              >
                <option value="">{s.sectorAll}</option>
                {sectors.map((sec) => (
                  <option key={sec.sector_en} value={sec.sector_en}>
                    {locale === "ar" ? sec.sector_ar : sec.sector_en} ({sec.count})
                  </option>
                ))}
              </select>
            </div>

            {/* Max Debt Ratio */}
            <div>
              <label className="block text-gray-400 text-sm mb-1.5">
                {s.debtRatioLabel} <span className="text-gray-600 text-xs">({s.debtRatioHint})</span>
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={maxDebtRatio}
                onChange={(e) => setMaxDebtRatio(e.target.value)}
                placeholder="33"
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none transition"
              />
            </div>

            {/* Max NC Income */}
            <div>
              <label className="block text-gray-400 text-sm mb-1.5">
                {s.ncIncomeLabel} <span className="text-gray-600 text-xs">({s.ncIncomeHint})</span>
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={maxNcIncome}
                onChange={(e) => setMaxNcIncome(e.target.value)}
                placeholder="5"
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none transition"
              />
            </div>

            {/* Min Market Cap */}
            <div>
              <label className="block text-gray-400 text-sm mb-1.5">{s.marketCapLabel}</label>
              <input
                type="number"
                min="0"
                value={minMarketCap}
                onChange={(e) => setMinMarketCap(e.target.value)}
                placeholder="0"
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none transition"
              />
            </div>

            {/* Sort */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-gray-400 text-sm mb-1.5">{s.sortByLabel}</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none transition"
                >
                  <option value="ticker">{s.sortOptions.ticker}</option>
                  <option value="name">{s.sortOptions.name}</option>
                  <option value="market_cap">{s.sortOptions.market_cap}</option>
                  <option value="debt_ratio">{s.sortOptions.debt_ratio}</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-1.5">&nbsp;</label>
                <select
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value)}
                  className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none transition"
                >
                  <option value="asc">{s.sortAsc}</option>
                  <option value="desc">{s.sortDesc}</option>
                </select>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 mt-5">
            <button
              onClick={fetchScreened}
              className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-lg font-medium text-sm transition flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              {s.apply}
            </button>
            <button
              onClick={reset}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-6 py-2.5 rounded-lg font-medium text-sm transition border border-gray-700"
            >
              {s.reset}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl overflow-hidden backdrop-blur-sm">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
            <h3 className="text-white font-semibold">{s.resultsTitle}</h3>
            {!loading && (
              <span className="text-sm text-gray-400">
                <span className="text-emerald-400 font-bold">{stocks.length}</span> {s.resultsCount}
                <span className="text-gray-600"> ({s.ofUniverse} {totalUniverse})</span>
              </span>
            )}
          </div>

          {loading ? (
            <div className="px-6 py-20 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-emerald-500 mb-3" />
              <p className="text-gray-400">{s.loading}</p>
            </div>
          ) : stocks.length === 0 ? (
            <div className="px-6 py-20 text-center">
              <p className="text-gray-500 text-lg">{s.noResults}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800 text-left">
                    <th className="px-6 py-3 text-gray-400 text-xs uppercase tracking-wider font-medium">{s.colTicker}</th>
                    <th className="px-4 py-3 text-gray-400 text-xs uppercase tracking-wider font-medium">{s.colName}</th>
                    <th className="px-4 py-3 text-gray-400 text-xs uppercase tracking-wider font-medium hidden md:table-cell">{s.colSector}</th>
                    <th className="px-4 py-3 text-gray-400 text-xs uppercase tracking-wider font-medium hidden lg:table-cell">{s.colMarketCap}</th>
                    <th className="px-4 py-3 text-gray-400 text-xs uppercase tracking-wider font-medium hidden lg:table-cell">{s.colDebtRatio}</th>
                    <th className="px-4 py-3 text-gray-400 text-xs uppercase tracking-wider font-medium">{s.colVerdict}</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {stocks.map((stock) => {
                    const badge = verdictBadge(stock.verdict, stock.is_halal);
                    const name = locale === "ar" ? stock.name_ar : stock.name_en;
                    const sectorName = locale === "ar" ? stock.sector_ar : stock.sector_en;
                    const debtPct = stock.ratios.debt_to_assets !== null ? (stock.ratios.debt_to_assets * 100).toFixed(1) + "%" : "—";
                    const ncPct = stock.ratios.non_compliant_income_ratio !== null ? (stock.ratios.non_compliant_income_ratio * 100).toFixed(2) + "%" : "—";

                    return (
                      <tr key={stock.ticker} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition group">
                        <td className="px-6 py-4">
                          <span className="font-mono text-white font-medium">{stock.ticker}</span>
                        </td>
                        <td className="px-4 py-4">
                          <span className="text-gray-200">{name}</span>
                        </td>
                        <td className="px-4 py-4 hidden md:table-cell">
                          <span className="text-gray-400 text-sm">{sectorName}</span>
                        </td>
                        <td className="px-4 py-4 hidden lg:table-cell">
                          <span className="text-gray-300 text-sm font-mono">{formatMarketCap(stock.market_cap, locale)}</span>
                        </td>
                        <td className="px-4 py-4 hidden lg:table-cell">
                          <span className={`text-sm font-mono ${stock.ratios.debt_to_assets !== null && stock.ratios.debt_to_assets > 0.33 ? "text-red-400" : "text-emerald-400"}`}>
                            {debtPct}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text} ${badge.border} border`}>
                            {badge.icon} {locale === "ar" ? stock.verdict_ar || name : stock.verdict.replace(/_/g, " ").toLowerCase()}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-right">
                          <Link
                            href={`/${locale}/stock/${stock.ticker}`}
                            className="text-emerald-400 hover:text-emerald-300 text-sm opacity-0 group-hover:opacity-100 transition whitespace-nowrap"
                          >
                            {s.viewDetails} →
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
