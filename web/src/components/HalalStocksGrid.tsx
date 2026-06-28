"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";

interface HalalStocksGridProps {
  dict: Dict;
  locale: string;
}

interface HalalStock {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
  market: string;
  currency: string;
  verdict: string;
  verdict_detail: string;
}

interface HalalStocksResponse {
  count: number;
  total_screened: number;
  stocks: HalalStock[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fallback data when API is unavailable
const FALLBACK_HALAL: HalalStock[] = [
  {
    ticker: "1120",
    name_en: "Al Rajhi Bank",
    name_ar: "مصرف الراجحي",
    sector_en: "Islamic Banking",
    sector_ar: "الخدمات المصرفية الإسلامية",
    market: "saudi",
    currency: "SAR",
    verdict: "COMPLIANT",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
  {
    ticker: "2222",
    name_en: "Saudi Aramco",
    name_ar: "أرامكو السعودية",
    sector_en: "Energy",
    sector_ar: "الطاقة",
    market: "saudi",
    currency: "SAR",
    verdict: "COMPLIANT",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
  {
    ticker: "7010",
    name_en: "STC Group",
    name_ar: "مجموعة إس تي سي",
    sector_en: "Telecommunications",
    sector_ar: "الاتصالات",
    market: "saudi",
    currency: "SAR",
    verdict: "COMPLIANT",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
  {
    ticker: "2010",
    name_en: "SABIC",
    name_ar: "سابك",
    sector_en: "Petrochemicals",
    sector_ar: "البتروكيماويات",
    market: "saudi",
    currency: "SAR",
    verdict: "COMPLIANT_WITH_OVERLAY",
    verdict_detail: "Permitted business. Monitor for impermissible income streams.",
  },
  {
    ticker: "2380",
    name_en: "Bank Albilad",
    name_ar: "بنك البلاد",
    sector_en: "Islamic Banking",
    sector_ar: "الخدمات المصرفية الإسلامية",
    market: "saudi",
    currency: "SAR",
    verdict: "COMPLIANT",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
  {
    ticker: "2280",
    name_en: "ADNOC Distribution",
    name_ar: "أدنوك التوزيع",
    sector_en: "Fuel Retail",
    sector_ar: "تجزئة الوقود",
    market: "saudi",
    currency: "SAR",
    verdict: "COMPLIANT",
    verdict_detail: "Passes both qualitative and quantitative Sharia screens.",
  },
];

export default function HalalStocksGrid({ dict, locale }: HalalStocksGridProps) {
  const [stocks, setStocks] = useState<HalalStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterSector, setFilterSector] = useState<string>("all");
  const [totalScreened, setTotalScreened] = useState(0);

  useEffect(() => {
    async function fetchHalal() {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/halal-stocks`);
        if (res.ok) {
          const data: HalalStocksResponse = await res.json();
          setStocks(data.stocks);
          setTotalScreened(data.total_screened);
        } else {
          setStocks(FALLBACK_HALAL);
          setTotalScreened(20);
        }
      } catch {
        setStocks(FALLBACK_HALAL);
        setTotalScreened(20);
      } finally {
        setLoading(false);
      }
    }
    fetchHalal();
  }, []);

  // Extract unique sectors for filter
  const sectors = Array.from(new Set(stocks.map((s) => s.sector_en))).sort();
  const sectorLabels: Record<string, string> = {};
  stocks.forEach((s) => {
    if (!sectorLabels[s.sector_en]) sectorLabels[s.sector_en] = s.sector_ar;
  });

  const filtered =
    filterSector === "all"
      ? stocks
      : stocks.filter((s) => s.sector_en === filterSector);

  const d = dict.discover || {
    title: "Halal Stock Universe",
    subtitle: "Every stock here has already passed Sharia screening",
    filterAll: "All Sectors",
    screened: "screened",
    passed: "passed",
    verifiedHalal: "Verified Halal",
    needsPurification: "Needs Purification",
    viewDetails: "View Details",
    loadingText: "Screening stocks...",
  };

  return (
    <section id="discover" className="py-20 md:py-28 bg-gradient-to-b from-mizan-green-pale/20 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-mizan-green/10 rounded-full mb-4">
            <span className="w-2 h-2 bg-mizan-green rounded-full animate-pulse" />
            <span className="text-sm font-medium text-mizan-green-dark font-arabic">
              {locale === "ar" ? "مفلتر مسبقاً" : "Pre-filtered"}
            </span>
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-4 font-arabic">
            {d.title}
          </h2>
          <p className="text-lg text-mizan-slate font-arabic max-w-2xl mx-auto">
            {d.subtitle}
          </p>
        </div>

        {/* Stats bar */}
        <div className="flex items-center justify-center gap-6 mb-8 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-mizan-green">{stocks.length}</span>
            <span className="text-mizan-slate font-arabic">
              {locale === "ar" ? "سهم حلال" : "halal stocks"}
            </span>
          </div>
          <div className="w-px h-8 bg-gray-200" />
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-mizan-slate">
              {totalScreened - stocks.length}
            </span>
            <span className="text-mizan-slate font-arabic">
              {locale === "ar" ? "مستبعد" : "filtered out"}
            </span>
          </div>
          <div className="w-px h-8 bg-gray-200" />
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-mizan-slate">{totalScreened}</span>
            <span className="text-mizan-slate font-arabic">
              {locale === "ar" ? "إجمالي" : "total screened"}
            </span>
          </div>
        </div>

        {/* Sector filter */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
          <button
            onClick={() => setFilterSector("all")}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors font-arabic ${
              filterSector === "all"
                ? "bg-mizan-green text-white"
                : "bg-gray-100 text-mizan-slate hover:bg-gray-200"
            }`}
          >
            {d.filterAll}
          </button>
          {sectors.map((sector) => (
            <button
              key={sector}
              onClick={() => setFilterSector(sector)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors font-arabic ${
                filterSector === sector
                  ? "bg-mizan-green text-white"
                  : "bg-gray-100 text-mizan-slate hover:bg-gray-200"
              }`}
            >
              {locale === "ar" ? sectorLabels[sector] : sector}
            </button>
          ))}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-3 border-mizan-green border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-mizan-slate font-arabic">{d.loadingText}</p>
          </div>
        )}

        {/* Stock grid */}
        {!loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((stock) => {
              const isPureCompliant = stock.verdict === "COMPLIANT";
              return (
                <Link
                  key={`${stock.ticker}-${stock.name_en}`}
                  href={`/${locale}/stock/${stock.ticker}`}
                  className="group bg-white rounded-2xl border-2 border-gray-100 hover:border-mizan-green/40 hover:shadow-lg transition-all p-5 cursor-pointer relative overflow-hidden block"
                >
                  {/* Verdict badge */}
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <span className="text-xs font-mono text-gray-400">{stock.ticker}</span>
                      <h3 className="text-lg font-bold text-mizan-ink font-arabic mt-0.5">
                        {locale === "ar" ? stock.name_ar : stock.name_en}
                      </h3>
                    </div>
                    <span
                      className={`px-2.5 py-1 text-xs font-bold rounded-full whitespace-nowrap ${
                        isPureCompliant
                          ? "bg-mizan-green/15 text-mizan-green-dark"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {isPureCompliant ? "✓ Halal" : "⚠ Halal*"}
                    </span>
                  </div>

                  {/* Sector + market */}
                  <div className="flex items-center gap-3 text-sm text-mizan-slate">
                    <span className="font-arabic">
                      {locale === "ar" ? stock.sector_ar : stock.sector_en}
                    </span>
                    {stock.market !== "saudi" && (
                      <>
                        <span className="text-gray-300">·</span>
                        <span className="uppercase text-xs font-medium">{stock.market}</span>
                      </>
                    )}
                  </div>

                  {/* Hover detail */}
                  <div className="mt-3 pt-3 border-t border-gray-50">
                    <p className="text-xs text-mizan-slate/70 font-arabic line-clamp-2">
                      {stock.verdict_detail}
                    </p>
                  </div>

                  {/* Hover arrow */}
                  <div className="absolute bottom-4 left-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-mizan-green text-sm font-medium">
                      {locale === "ar" ? "عرض التفاصيل ←" : "View details →"}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}

        {/* Disclaimer */}
        {!loading && filtered.length === 0 && (
          <div className="text-center py-12">
            <p className="text-mizan-slate font-arabic">
              {locale === "ar"
                ? "لا توجد أسهم متوافقة في هذا القطاع حالياً."
                : "No compliant stocks in this sector yet."}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
