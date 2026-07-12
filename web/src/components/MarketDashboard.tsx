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

const FALLBACK_DATA: MarketData = {
  overview: {
    total_stocks: 49,
    halal_count: 14,
    halal_pct: 28.6,
    non_compliant_count: 35,
    purification_count: 0,
    total_market_cap: 1.2e13,
    halal_market_cap: 7.5e12,
    halal_market_share_pct: 62.5,
    sectors_count: 16,
    standard: "AAOIFI Standard No. 21",
  },
  verdict_distribution: { COMPLIANT: 14, COMPLIANT_WITH_OVERLAY: 0, COMPLIANT_WITH_PURIFICATION: 0, NON_COMPLIANT: 35 },
  sectors: [
    { sector_en: "Islamic Banking", sector_ar: "الخدمات المصرفية الإسلامية", total: 4, compliant: 4, non_compliant: 0, purification: 0, total_market_cap: 5e11, halal_market_cap: 5e11, compliance_rate: 100, halal_market_share: 100 },
    { sector_en: "Energy", sector_ar: "الطاقة", total: 3, compliant: 2, non_compliant: 1, purification: 0, total_market_cap: 7e12, halal_market_cap: 6.5e12, compliance_rate: 66.7, halal_market_share: 92.8 },
    { sector_en: "Telecommunications", sector_ar: "الاتصالات", total: 2, compliant: 1, non_compliant: 1, purification: 0, total_market_cap: 3e11, halal_market_cap: 2.5e11, compliance_rate: 50, halal_market_share: 83.3 },
    { sector_en: "Conventional Banking", sector_ar: "الخدمات المصرفية التقليدية", total: 5, compliant: 0, non_compliant: 5, purification: 0, total_market_cap: 4e11, halal_market_cap: 0, compliance_rate: 0, halal_market_share: 0 },
  ],
  top_halal_stocks: [
    { ticker: "2222", name_en: "Saudi Aramco", name_ar: "أرامكو السعودية", sector_en: "Energy", sector_ar: "الطاقة", market_cap: 6.4e12, currency: "SAR", verdict: "COMPLIANT", verdict_ar: "متوافق", is_halal: true, debt_to_assets: 19.2 },
    { ticker: "1120", name_en: "Al Rajhi Bank", name_ar: "مصرف الراجحي", sector_en: "Islamic Banking", sector_ar: "الخدمات المصرفية الإسلامية", market_cap: 3.98e11, currency: "SAR", verdict: "COMPLIANT", verdict_ar: "متوافق", is_halal: true, debt_to_assets: 8.5 },
    { ticker: "7010", name_en: "STC Group", name_ar: "مجموعة إس تي سي", sector_en: "Telecommunications", sector_ar: "الاتصالات", market_cap: 2.17e11, currency: "SAR", verdict: "COMPLIANT", verdict_ar: "متوافق", is_halal: true, debt_to_assets: 9.4 },
  ],
  best_ratio_stocks: [
    { ticker: "1150", name_en: "Alinma Bank", name_ar: "مصرف الإنماء", sector_en: "Islamic Banking", sector_ar: "الخدمات المصرفية الإسلامية", market_cap: 7.4e10, currency: "SAR", verdict: "COMPLIANT", verdict_ar: "متوافق", is_halal: true, debt_to_assets: 6.9 },
    { ticker: "1120", name_en: "Al Rajhi Bank", name_ar: "مصرف الراجحي", sector_en: "Islamic Banking", sector_ar: "الخدمات المصرفية الإسلامية", market_cap: 3.98e11, currency: "SAR", verdict: "COMPLIANT", verdict_ar: "متوافق", is_halal: true, debt_to_assets: 8.5 },
    { ticker: "7010", name_en: "STC Group", name_ar: "مجموعة إس تي سي", sector_en: "Telecommunications", sector_ar: "الاتصالات", market_cap: 2.17e11, currency: "SAR", verdict: "COMPLIANT", verdict_ar: "متوافق", is_halal: true, debt_to_assets: 9.4 },
  ],
};

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
  const isAr = locale === "ar";

  useEffect(() => {
    fetch(`${API_URL}/api/market`)
      .then((res) => res.json())
      .then((d: MarketData) => setData(d))
      .catch(() => setData(FALLBACK_DATA))
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-mizan-green text-xl font-arabic">
          {isAr ? "...جاري تحميل لوحة السوق" : "Loading market dashboard..."}
        </div>
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

        {/* Compliance Donut + Distribution */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          {/* Donut visualization */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
            <h3 className="text-xl font-bold text-mizan-ink mb-6 font-arabic">
              {isAr ? "توزيع الامتثال" : "Compliance Distribution"}
            </h3>
            <div className="flex items-center justify-center mb-6">
              <ComplianceDonut
                halal={ov.halal_count}
                nonCompliant={ov.non_compliant_count}
                purification={ov.purification_count}
              />
            </div>
            <div className="space-y-3">
              <DistributionBar
                label={isAr ? "متوافق" : "Compliant"}
                count={ov.halal_count}
                total={ov.total_stocks}
                color="bg-emerald-500"
              />
              <DistributionBar
                label={isAr ? "غير متوافق" : "Non-Compliant"}
                count={ov.non_compliant_count}
                total={ov.total_stocks}
                color="bg-red-400"
              />
            </div>
          </div>

          {/* Market Cap Info */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
            <h3 className="text-xl font-bold text-mizan-ink mb-6 font-arabic">
              {isAr ? "رأس المال السوقي" : "Market Capitalization"}
            </h3>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="text-sm text-mizan-slate font-arabic">{isAr ? "إجمالي السوق" : "Total Market"}</span>
                  <span className="text-2xl font-bold text-mizan-ink">{formatMarketCap(ov.total_market_cap)}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="text-sm text-mizan-slate font-arabic">{isAr ? "الأسهم الحلال" : "Halal Stocks"}</span>
                  <span className="text-2xl font-bold text-emerald-600">{formatMarketCap(ov.halal_market_cap)}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full h-3 transition-all duration-1000"
                    style={{ width: `${ov.halal_market_share_pct}%` }}
                  />
                </div>
                <span className="text-xs text-mizan-slate mt-1">{ov.halal_market_share_pct}% {isAr ? "حلال" : "halal"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sector Heatmap */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 md:p-8 mb-12">
          <h3 className="text-xl font-bold text-mizan-ink mb-6 font-arabic">
            {isAr ? "خريطة قطاعات الامتثال" : "Sector Compliance Heatmap"}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {data.sectors.map((sector) => (
              <div
                key={sector.sector_en}
                className={`relative overflow-hidden rounded-xl bg-gradient-to-br ${heatColor(sector.compliance_rate)} p-4 text-white shadow-md hover:scale-105 transition-transform cursor-pointer`}
              >
                <div className="text-xs font-medium opacity-90 mb-1">
                  {isAr ? sector.sector_ar : sector.sector_en}
                </div>
                <div className="text-2xl font-bold">{sector.compliance_rate}%</div>
                <div className="text-xs opacity-80 mt-1">
                  {sector.compliant}/{sector.total} {isAr ? "حلال" : "halal"}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Halal Stocks by Market Cap */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
            <div className="bg-gradient-to-r from-mizan-green to-mizan-green-dark px-6 py-4">
              <h3 className="text-lg font-bold text-white font-arabic">
                {isAr ? "أكبر الأسهم الحلال" : "Top Halal Stocks by Market Cap"}
              </h3>
            </div>
            <div className="divide-y divide-gray-50">
              {data.top_halal_stocks.slice(0, 8).map((stock, i) => {
                const badge = verdictBadge(stock.verdict, locale);
                return (
                  <Link
                    key={stock.ticker}
                    href={`/${locale}/stock/${stock.ticker}`}
                    className="flex items-center gap-4 px-6 py-3 hover:bg-mizan-green-pale/30 transition-colors group"
                  >
                    <span className="text-lg font-bold text-mizan-slate/40 w-6">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-mizan-ink truncate group-hover:text-mizan-green transition-colors">
                        {isAr ? stock.name_ar : stock.name_en}
                      </div>
                      <div className="text-xs text-mizan-slate">
                        {stock.ticker} · {isAr ? stock.sector_ar : stock.sector_en}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-mizan-ink">{formatMarketCap(stock.market_cap, stock.currency)}</div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Best Ratios */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4">
              <h3 className="text-lg font-bold text-white font-arabic">
                {isAr ? "أفضل نسب الدين" : "Lowest Debt Ratios"}
              </h3>
            </div>
            <div className="divide-y divide-gray-50">
              {data.best_ratio_stocks.map((stock, i) => (
                <Link
                  key={stock.ticker}
                  href={`/${locale}/stock/${stock.ticker}`}
                  className="flex items-center gap-4 px-6 py-3 hover:bg-amber-50 transition-colors group"
                >
                  <span className="text-lg font-bold text-amber-300 w-6">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-mizan-ink truncate group-hover:text-amber-600 transition-colors">
                      {isAr ? stock.name_ar : stock.name_en}
                    </div>
                    <div className="text-xs text-mizan-slate">{stock.ticker}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-emerald-600">
                      {typeof stock.debt_to_assets === "number" ? `${stock.debt_to_assets.toFixed(1)}%` : "—"}
                    </div>
                    <div className="text-xs text-mizan-slate">{isAr ? "دين/أصول" : "Debt/Assets"}</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Full Sector Table */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-lg font-bold text-mizan-ink font-arabic">
              {isAr ? "تفاصيل القطاعات" : "Sector Breakdown Details"}
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-medium text-mizan-slate uppercase tracking-wider font-arabic">
                    {isAr ? "القطاع" : "Sector"}
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-mizan-slate uppercase tracking-wider">
                    {isAr ? "الإجمالي" : "Total"}
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-mizan-slate uppercase tracking-wider">
                    {isAr ? "حلال" : "Halal"}
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-mizan-slate uppercase tracking-wider">
                    {isAr ? "غير متوافق" : "Non-Compliant"}
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-mizan-slate uppercase tracking-wider">
                    {isAr ? "نسبة الامتثال" : "Compliance Rate"}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.sectors.map((sector) => (
                  <tr key={sector.sector_en} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-mizan-ink font-arabic">
                      {isAr ? sector.sector_ar : sector.sector_en}
                    </td>
                    <td className="text-center px-4 py-4 text-sm text-mizan-slate">{sector.total}</td>
                    <td className="text-center px-4 py-4 text-sm font-semibold text-emerald-600">{sector.compliant}</td>
                    <td className="text-center px-4 py-4 text-sm text-red-400">{sector.non_compliant}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 max-w-[200px] bg-gray-100 rounded-full h-2">
                          <div
                            className={`bg-gradient-to-r ${heatColor(sector.compliance_rate)} rounded-full h-2 transition-all duration-700`}
                            style={{ width: `${sector.compliance_rate}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold text-mizan-ink w-12 text-right">{sector.compliance_rate}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Standard Reference */}
        <div className="mt-8 text-center">
          <p className="text-sm text-mizan-slate font-arabic">
            {isAr
              ? `وفقًا لـ ${ov.standard} · البيانات لـ ${ov.total_stocks} سهمًا في السوق السعودي`
              : `According to ${ov.standard} · Data covers ${ov.total_stocks} stocks on the Saudi market`}
          </p>
        </div>
      </div>
    </section>
  );
}

function MetricCard({ label, value, subValue, icon, color }: { label: string; value: string; subValue?: string; icon: string; color: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5 hover:shadow-lg transition-shadow">
      <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center text-white text-lg mb-3`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-mizan-ink">{value}</div>
      {subValue && <div className="text-sm text-emerald-600 font-medium">{subValue}</div>}
      <div className="text-xs text-mizan-slate mt-1">{label}</div>
    </div>
  );
}

function ComplianceDonut({ halal, nonCompliant, purification }: { halal: number; nonCompliant: number; purification: number }) {
  const total = halal + nonCompliant + purification;
  if (total === 0) return null;
  const halalPct = (halal / total) * 100;
  const radius = 70;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="relative w-44 h-44">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 180 180">
        <circle cx="90" cy="90" r={radius} fill="none" stroke="#fee2e2" strokeWidth="18" />
        <circle
          cx="90" cy="90" r={radius} fill="none" stroke="#10b981" strokeWidth="18"
          strokeDasharray={`${(halalPct / 100) * circumference} ${circumference}`}
          strokeLinecap="round"
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-mizan-ink">{halalPct.toFixed(0)}%</span>
        <span className="text-xs text-mizan-slate">Halal</span>
      </div>
    </div>
  );
}

function DistributionBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-mizan-slate w-24 font-arabic">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`${color} rounded-full h-2 transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-medium text-mizan-ink w-8 text-right">{count}</span>
    </div>
  );
}
