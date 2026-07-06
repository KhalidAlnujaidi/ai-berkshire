"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";
import type { Locale } from "@/i18n";

interface MarketOverview {
  total_stocks: number;
  halal_count: number;
  halal_pct: number;
  non_compliant_count: number;
  purification_count: number;
  total_market_cap: number;
  halal_market_cap: number;
  halal_market_share_pct: number;
  sectors_count: number;
  standard: string;
}

interface SectorData {
  sector_en: string;
  sector_ar: string;
  total: number;
  compliant: number;
  non_compliant: number;
  purification: number;
  total_market_cap: number;
  halal_market_cap: number;
  compliance_rate: number;
  halal_market_share: number;
}

interface TopStock {
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
  debt_to_assets: number;
}

interface MarketData {
  overview: MarketOverview;
  verdict_distribution: Record<string, number>;
  sectors: SectorData[];
  top_halal_stocks: TopStock[];
  best_ratio_stocks: TopStock[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function formatMarketCap(value: number, currency: string = "SAR"): string {
  if (value >= 1e12) return `${(value / 1e12).toFixed(2)}T ${currency}`;
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B ${currency}`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M ${currency}`;
  return `${value.toLocaleString()} ${currency}`;
}

function heatColor(rate: number): string {
  if (rate >= 100) return "from-emerald-500 to-emerald-600";
  if (rate >= 75) return "from-green-400 to-green-500";
  if (rate >= 50) return "from-yellow-400 to-yellow-500";
  if (rate >= 25) return "from-orange-400 to-orange-500";
  return "from-red-400 to-red-500";
}

function verdictBadge(verdict: string, locale: string): { label: string; color: string } {
  const isAr = locale === "ar";
  switch (verdict) {
    case "COMPLIANT":
      return { label: isAr ? "متوافق" : "✓ Halal", color: "bg-emerald-100 text-emerald-700 border-emerald-200" };
    case "COMPLIANT_WITH_OVERLAY":
    case "COMPLIANT_WITH_PURIFICATION":
      return { label: isAr ? "يتطلب تنقية" : "⚠ Purify", color: "bg-amber-100 text-amber-700 border-amber-200" };
    default:
      return { label: isAr ? "غير متوافق" : "✗ Haram", color: "bg-red-100 text-red-700 border-red-200" };
  }
}

interface Props {
  dict: Dict;
  locale: Locale;
}

export default function MarketDashboard({ dict, locale }: Props) {
  const [data, setData] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isAr = locale === "ar";

  useEffect(() => {
    fetch(`${API_URL}/api/market`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((d: MarketData) => {
        setData(d);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load market data");
        setData(null);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-mizan-green text-xl font-arabic">
          {isAr ? "...جاري تحميل لوحة السوق" : "Loading market dashboard..."}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-100 mb-4">
          <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-mizan-ink mb-2 font-arabic">
          {isAr ? "تعذر تحميل بيانات السوق" : "Market data unavailable"}
        </h2>
        <p className="text-mizan-slate font-arabic">
          {isAr
            ? `تعذر الاتصال بالخادم. يرجى التحقق من أن الخادم قيد التشغيل. (${error})`
            : `Could not connect to market data API. Please ensure the backend is running. (${error})`}
        </p>
      </div>
    );
  }

  const ov = data.overview;

  return (
    <section className="py-12 md:py-20 bg-gradient-to-b from-mizan-green-pale/30 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-3 font-arabic">
            {isAr ? "لوحة السوق" : "Market Dashboard"}
          </h1>
          <p className="text-mizan-slate text-lg font-arabic">
            {isAr
              ? "نظرة شاملة على امتثال سوق الأسهم السعودي للشريعة الإسلامية"
              : "Comprehensive overview of Sharia compliance across the Saudi stock market"}
          </p>
          <div className="text-xs text-mizan-slate/50 mt-1 font-arabic">
            {isAr ? "المصدر: بيانات مباشرة من تداول" : "Source: Live data from Tadawul"}
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          <MetricCard
            label={isAr ? "إجمالي الأسهم" : "Total Stocks"}
            value={ov.total_stocks.toString()}
            icon="📊"
            color="from-blue-500 to-blue-600"
          />
          <MetricCard
            label={isAr ? "أسهم حلال" : "Halal Stocks"}
            value={ov.halal_count.toString()}
            subValue={`${ov.halal_pct}%`}
            icon="✓"
            color="from-emerald-500 to-emerald-600"
          />
          <MetricCard
            label={isAr ? "قطاعات" : "Sectors"}
            value={ov.sectors_count.toString()}
            icon="🏭"
            color="from-purple-500 to-purple-600"
          />
          <MetricCard
            label={isAr ? "الحصة السوقية الحلال" : "Halal Market Share"}
            value={`${ov.halal_market_share_pct}%`}
            icon="💰"
            color="from-amber-500 to-amber-600"
          />
        </div>
      </div>
    </section>
  );
}

function MetricCard({
  label,
  value,
  subValue,
  icon,
  color,
}: {
  label: string;
  value: string;
  subValue?: string;
  icon: string;
  color: string;
}) {
  return (
    <div className={`rounded-2xl bg-gradient-to-br ${color} p-5 text-white shadow-lg`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-2xl md:text-3xl font-bold">{value}</div>
      {subValue && <div className="text-sm opacity-80">{subValue}</div>}
      <div className="text-xs mt-1 opacity-70">{label}</div>
    </div>
  );
}