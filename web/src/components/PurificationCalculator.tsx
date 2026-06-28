"use client";

import { useState, useEffect } from "react";
import type { Dict } from "@/i18n/ar";

interface PurificationCalculatorProps {
  dict: Dict;
  locale: string;
}

interface StockData {
  ticker: string;
  name: string;
  non_compliant_income: number;
  total_revenue: number;
  verdict: string;
}

const FALLBACK_STOCKS: StockData[] = [
  { ticker: "2222", name: "Saudi Aramco", non_compliant_income: 1200000000, total_revenue: 44000000000, verdict: "COMPLIANT_WITH_PURIFICATION" },
  { ticker: "2010", name: "Saudi Basic Industries", non_compliant_income: 800000000, total_revenue: 50000000000, verdict: "COMPLIANT_WITH_PURIFICATION" },
  { ticker: "1120", name: "Al Rajhi Bank", non_compliant_income: 0, total_revenue: 50000000000, verdict: "COMPLIANT" },
  { ticker: "1180", name: "Saudi National Bank", non_compliant_income: 5000000000, total_revenue: 40000000000, verdict: "NON-COMPLIANT" },
  { ticker: "7010", name: "STC", non_compliant_income: 200000000, total_revenue: 70000000000, verdict: "COMPLIANT_WITH_PURIFICATION" },
];

export default function PurificationCalculator({ dict, locale }: PurificationCalculatorProps) {
  const t = dict.purification;
  const [mode, setMode] = useState<"stock" | "manual">("stock");
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [selectedTicker, setSelectedTicker] = useState("");
  const [dividends, setDividends] = useState("");
  const [manualNCIncome, setManualNCIncome] = useState("");
  const [manualRevenue, setManualRevenue] = useState("");
  const [result, setResult] = useState<{
    amountToPurify: number;
    ratio: number;
    formula: string;
  } | null>(null);

  useEffect(() => {
    // Fetch stocks that need purification
    fetch("/api/halal-stocks")
      .then((r) => r.json())
      .then((data) => {
        if (data.stocks && data.stocks.length > 0) {
          const impureStocks = data.stocks
            .filter((s: StockData) => s.verdict === "COMPLIANT_WITH_PURIFICATION")
            .map((s: StockData) => ({
              ticker: s.ticker,
              name: locale === "ar" ? (s as any).name_ar : s.name,
              non_compliant_income: (s as any).non_compliant_income || 0,
              total_revenue: (s as any).total_revenue || 0,
              verdict: s.verdict,
            }));
          setStocks(impureStocks.length > 0 ? impureStocks : FALLBACK_STOCKS);
        }
      })
      .catch(() => setStocks(FALLBACK_STOCKS));
  }, [locale]);

  const calculate = () => {
    let ncIncome = 0;
    let totalRev = 0;
    let div = parseFloat(dividends) || 0;

    if (mode === "stock") {
      const stock = stocks.find((s) => s.ticker === selectedTicker);
      if (!stock) return;
      ncIncome = stock.non_compliant_income;
      totalRev = stock.total_revenue;
    } else {
      ncIncome = parseFloat(manualNCIncome) || 0;
      totalRev = parseFloat(manualRevenue) || 0;
    }

    if (totalRev === 0 || div === 0) return;

    const ratio = ncIncome / totalRev;
    const amountToPurify = div * ratio;

    setResult({
      amountToPurify,
      ratio: ratio * 100,
      formula: `${div.toLocaleString()} × (${ncIncome.toLocaleString()} ÷ ${totalRev.toLocaleString()})`,
    });
  };

  const fmtSAR = (n: number) =>
    n.toLocaleString(locale === "ar" ? "ar-SA" : "en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  return (
    <section className="py-20 bg-gradient-to-b from-white to-amber-50/20">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-1.5 rounded-full bg-amber-100 text-amber-700 text-sm font-medium mb-4 font-arabic">
            {locale === "ar" ? "✨ طهّر مالك" : "✨ Purify Your Wealth"}
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-3 font-arabic">
            {t.title}
          </h2>
          <p className="text-lg text-mizan-slate max-w-2xl mx-auto font-arabic">
            {t.subtitle}
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Calculator Form */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
            {/* Mode Toggle */}
            <div className="flex gap-2 p-1 bg-gray-100 rounded-xl mb-6">
              <button
                onClick={() => setMode("stock")}
                className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all font-arabic ${
                  mode === "stock"
                    ? "bg-white text-mizan-green shadow-sm"
                    : "text-mizan-slate hover:text-mizan-ink"
                }`}
              >
                {t.selectStockMode}
              </button>
              <button
                onClick={() => setMode("manual")}
                className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all font-arabic ${
                  mode === "manual"
                    ? "bg-white text-mizan-green shadow-sm"
                    : "text-mizan-slate hover:text-mizan-ink"
                }`}
              >
                {t.manualMode}
              </button>
            </div>

            {/* Stock Mode */}
            {mode === "stock" ? (
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-mizan-ink mb-2 font-arabic">
                    {t.stockLabel}
                  </label>
                  <select
                    value={selectedTicker}
                    onChange={(e) => setSelectedTicker(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic bg-white"
                  >
                    <option value="">{t.stockHint}</option>
                    {stocks.map((s) => (
                      <option key={s.ticker} value={s.ticker}>
                        {s.ticker} — {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-mizan-ink mb-2 font-arabic">
                    {t.nonCompliantIncomeLabel}
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      value={manualNCIncome}
                      onChange={(e) => setManualNCIncome(e.target.value)}
                      placeholder="0"
                      className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                      dir={locale === "ar" ? "rtl" : "ltr"}
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                      {locale === "ar" ? "ر.س" : "SAR"}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-mizan-ink mb-2 font-arabic">
                    {t.totalRevenueLabel}
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      value={manualRevenue}
                      onChange={(e) => setManualRevenue(e.target.value)}
                      placeholder="0"
                      className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                      dir={locale === "ar" ? "rtl" : "ltr"}
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                      {locale === "ar" ? "ر.س" : "SAR"}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Dividends — always shown */}
            <div className="mt-5">
              <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                {t.dividendsLabel}
              </label>
              <p className="text-xs text-mizan-slate mb-2 font-arabic">{t.dividendsHint}</p>
              <div className="relative">
                <input
                  type="number"
                  value={dividends}
                  onChange={(e) => setDividends(e.target.value)}
                  placeholder="0"
                  className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                  dir={locale === "ar" ? "rtl" : "ltr"}
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                  {locale === "ar" ? "ر.س" : "SAR"}
                </span>
              </div>
            </div>

            {/* Calculate Button */}
            <button
              onClick={calculate}
              className="w-full mt-6 px-6 py-3.5 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-xl transition-colors shadow-sm font-arabic"
            >
              {t.calculate}
            </button>
          </div>

          {/* Results */}
          <div className="space-y-6">
            {result ? (
              <>
                <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-2xl p-8 shadow-lg border-2 border-amber-300/30">
                  <h3 className="text-lg font-semibold text-mizan-ink mb-6 font-arabic">
                    {t.resultTitle}
                  </h3>

                  {/* Non-Compliant Ratio */}
                  <div className="flex items-center justify-between pb-4 border-b border-gray-200/50 mb-4">
                    <span className="text-mizan-slate font-arabic">
                      {t.nonCompliantIncomeLabel}
                    </span>
                    <span className="text-xl font-bold text-amber-600">
                      {result.ratio.toFixed(2)}%
                    </span>
                  </div>

                  {/* Formula */}
                  <div className="bg-white/60 rounded-xl p-4 mb-4">
                    <p className="text-xs text-mizan-slate mb-1 font-arabic">{t.formula}</p>
                    <p className="text-sm font-mono text-mizan-ink" dir="ltr">
                      {result.formula}
                    </p>
                  </div>

                  {/* Amount to Purify */}
                  <div className="bg-amber-600 rounded-xl p-5 text-white">
                    <p className="text-sm opacity-90 font-arabic mb-1">{t.amountToPurify}</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold">{fmtSAR(result.amountToPurify)}</span>
                      <span className="text-lg opacity-90">{locale === "ar" ? "ر.س" : "SAR"}</span>
                    </div>
                  </div>
                </div>

                {/* How to Purify */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                  <h4 className="font-semibold text-mizan-ink mb-4 flex items-center gap-2 font-arabic">
                    <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {t.howToPurify}
                  </h4>
                  <ol className="space-y-3">
                    {t.howToSteps.map((step, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-amber-100 text-amber-600 text-xs font-bold flex items-center justify-center mt-0.5">
                          {i + 1}
                        </span>
                        <span className="text-sm text-mizan-slate font-arabic">{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </>
            ) : (
              <div className="bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 p-8 flex items-center justify-center min-h-[300px]">
                <div className="text-center">
                  <svg className="w-12 h-12 text-amber-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                  </svg>
                  <p className="text-mizan-slate font-arabic">{t.noStockSelected}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
