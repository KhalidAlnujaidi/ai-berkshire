"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";

interface EducationCenterProps {
  dict: Dict;
  locale: string;
}

interface MarketStats {
  total_stocks: number;
  halal_count: number;
  halal_pct: number;
  non_compliant_count: number;
  purification_count: number;
  sectors: Array<{
    sector_en: string;
    sector_ar: string;
    total: number;
    compliant: number;
    non_compliant: number;
    compliance_rate: number;
  }>;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function EducationCenter({ dict, locale }: EducationCenterProps) {
  const t = dict.education;
  const [stats, setStats] = useState<MarketStats | null>(null);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  useEffect(() => {
    fetch(`${API_URL}/api/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  const ratios = [
    { name: t.ratio1Name, threshold: t.ratio1Threshold, desc: t.ratio1Desc, icon: "📊", color: "blue" },
    { name: t.ratio2Name, threshold: t.ratio2Threshold, desc: t.ratio2Desc, icon: "🏦", color: "indigo" },
    { name: t.ratio3Name, threshold: t.ratio3Threshold, desc: t.ratio3Desc, icon: "💰", color: "purple" },
    { name: t.ratio4Name, threshold: t.ratio4Threshold, desc: t.ratio4Desc, icon: "📋", color: "cyan" },
    { name: t.ratio5Name, threshold: t.ratio5Threshold, desc: t.ratio5Desc, icon: "⚠️", color: "amber" },
    { name: t.ratio6Name, threshold: t.ratio6Threshold, desc: t.ratio6Desc, icon: "🏗️", color: "teal" },
  ];

  const purifSteps = [t.purifStep1, t.purifStep2, t.purifStep3, t.purifStep4];

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-mizan-green-dark via-mizan-green to-emerald-600 text-white py-20 md:py-28">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-yellow-200 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <span className="inline-block px-4 py-1.5 mb-6 text-sm font-medium bg-white/20 backdrop-blur-sm rounded-full">
            {t.heroBadge}
          </span>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 font-arabic">{t.title}</h1>
          <p className="text-lg md:text-xl text-white/90 font-arabic">{t.subtitle}</p>
        </div>
      </section>

      {/* Live Market Stats */}
      {stats && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 relative z-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: t.statTotalStocks, value: stats.total_stocks, icon: "📈" },
              { label: t.statHalalRate, value: `${stats.halal_pct}%`, icon: "✅" },
              { label: t.statSectors, value: stats.sectors.length, icon: "🏭" },
              { label: t.statStandard, value: "AAOIFI 21", icon: "📜" },
            ].map((s, i) => (
              <div
                key={i}
                className="bg-white rounded-2xl shadow-lg border border-gray-100 p-5 text-center hover:shadow-xl transition-shadow"
              >
                <div className="text-3xl mb-2">{s.icon}</div>
                <div className="text-2xl md:text-3xl font-bold text-mizan-ink">{s.value}</div>
                <div className="text-sm text-mizan-slate mt-1 font-arabic">{s.label}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* The 6 Financial Ratios */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-3 font-arabic">{t.sectionRatios}</h2>
          <p className="text-lg text-mizan-slate max-w-3xl mx-auto font-arabic">{t.sectionRatiosDesc}</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {ratios.map((ratio, i) => (
            <div
              key={i}
              className="group bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg transition-all p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-mizan-green-pale flex items-center justify-center text-2xl">
                  {ratio.icon}
                </div>
                <span className="px-3 py-1 text-sm font-bold text-mizan-green bg-mizan-green-pale rounded-lg">
                  {ratio.threshold}
                </span>
              </div>
              <h3 className="text-lg font-bold text-mizan-ink mb-2 font-arabic">{ratio.name}</h3>
              <p className="text-sm text-mizan-slate leading-relaxed font-arabic">{ratio.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Qualitative Screen — Permitted vs Prohibited */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-3 font-arabic">{t.sectionQualitative}</h2>
            <p className="text-lg text-mizan-slate max-w-3xl mx-auto font-arabic">{t.sectionQualitativeDesc}</p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {/* Prohibited */}
            <div className="bg-red-50 rounded-2xl border-2 border-red-100 p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-red-700 font-arabic">{t.prohibitedTitle}</h3>
              </div>
              <p className="text-sm text-red-600 mb-4 font-arabic">{t.prohibitedDesc}</p>
              <ul className="space-y-3">
                {t.prohibited.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-mizan-ink">
                    <span className="text-red-500 mt-0.5">✗</span>
                    <span className="font-arabic">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Permitted */}
            <div className="bg-green-50 rounded-2xl border-2 border-green-100 p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-green-700 font-arabic">{t.permittedTitle}</h3>
              </div>
              <p className="text-sm text-green-600 mb-4 font-arabic">{t.permittedDesc}</p>
              <ul className="space-y-3">
                {t.permitted.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-mizan-ink">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span className="font-arabic">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Income Purification */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-100 mb-4">
            <span className="text-3xl">🤲</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-3 font-arabic">{t.sectionPurification}</h2>
          <p className="text-lg text-mizan-slate max-w-3xl mx-auto font-arabic">{t.sectionPurificationDesc}</p>
        </div>
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="divide-y divide-gray-100">
            {purifSteps.map((step, i) => (
              <div key={i} className="flex items-start gap-4 p-6 hover:bg-gray-50 transition-colors">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-white flex items-center justify-center font-bold text-lg">
                  {i + 1}
                </div>
                <p className="text-mizan-ink pt-1.5 font-arabic">{step}</p>
              </div>
            ))}
          </div>
          <div className="bg-amber-50 border-t border-amber-100 p-4">
            <p className="text-sm text-amber-700 text-center font-arabic">💡 {t.purifNote}</p>
          </div>
        </div>
      </section>

      {/* Market Compliance Table */}
      {stats && stats.sectors.length > 0 && (
        <section className="bg-gray-50 py-20">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-3 font-arabic">{t.marketOverview}</h2>
            </div>
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-mizan-green text-white">
                      <th className="px-6 py-4 text-right text-sm font-semibold font-arabic">{t.sectorCol}</th>
                      <th className="px-4 py-4 text-center text-sm font-semibold">{t.totalCol}</th>
                      <th className="px-4 py-4 text-center text-sm font-semibold">{t.halalCol}</th>
                      <th className="px-6 py-4 text-center text-sm font-semibold font-arabic">{t.rateCol}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {stats.sectors
                      .filter((s) => s.sector_en)
                      .map((sector, i) => (
                        <tr key={i} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-3 text-mizan-ink font-medium font-arabic">
                            {locale === "ar" ? sector.sector_ar || sector.sector_en : sector.sector_en}
                          </td>
                          <td className="px-4 py-3 text-center text-mizan-slate">{sector.total}</td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-green-600 font-semibold">{sector.compliant}</span>
                            <span className="text-mizan-slate"> / {sector.total}</span>
                          </td>
                          <td className="px-6 py-3">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden min-w-[60px]">
                                <div
                                  className={`h-full rounded-full transition-all duration-500 ${
                                    sector.compliance_rate >= 50
                                      ? "bg-green-500"
                                      : sector.compliance_rate > 0
                                        ? "bg-amber-500"
                                        : "bg-red-500"
                                  }`}
                                  style={{ width: `${sector.compliance_rate}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium text-mizan-slate min-w-[45px]">
                                {sector.compliance_rate}%
                              </span>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* FAQ */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-3 font-arabic">{t.sectionFaq}</h2>
        </div>
        <div className="space-y-4">
          {t.faq.map((item, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden"
            >
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between gap-4 p-5 text-right hover:bg-gray-50 transition-colors"
              >
                <span className="font-semibold text-mizan-ink font-arabic">{item.q}</span>
                <svg
                  className={`w-5 h-5 text-mizan-green flex-shrink-0 transition-transform ${openFaq === i ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {openFaq === i && (
                <div className="px-5 pb-5 text-mizan-slate leading-relaxed animate-fade-in font-arabic">
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="bg-gradient-to-br from-mizan-green-dark via-mizan-green to-emerald-600 rounded-3xl p-10 md:p-16 text-center text-white">
          <h2 className="text-2xl md:text-3xl font-bold mb-6 font-arabic">{t.ctaTitle}</h2>
          <Link
            href={`/${locale}#checker`}
            className="inline-block px-8 py-4 bg-white text-mizan-green-dark font-bold rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all font-arabic"
          >
            {t.ctaButton}
          </Link>
        </div>
      </section>
    </>
  );
}
