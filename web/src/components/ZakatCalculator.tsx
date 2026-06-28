"use client";

import { useState } from "react";
import type { Dict } from "@/i18n/ar";

interface ZakatCalculatorProps {
  dict: Dict;
  locale: string;
}

export default function ZakatCalculator({ dict, locale }: ZakatCalculatorProps) {
  const t = dict.zakat;
  const [portfolioValue, setPortfolioValue] = useState("");
  const [cash, setCash] = useState("");
  const [receivables, setReceivables] = useState("");
  const [liabilities, setLiabilities] = useState("");
  const [goldPrice, setGoldPrice] = useState("280");
  const [result, setResult] = useState<{
    eligibleAssets: number;
    nisab: number;
    zakatDue: number;
    isAboveNisab: boolean;
  } | null>(null);

  const calculate = () => {
    const p = parseFloat(portfolioValue) || 0;
    const c = parseFloat(cash) || 0;
    const r = parseFloat(receivables) || 0;
    const l = parseFloat(liabilities) || 0;
    const gp = parseFloat(goldPrice) || 280;

    const totalAssets = p + c + r;
    const eligibleAssets = Math.max(0, totalAssets - l);
    const nisab = gp * 85; // 85 grams of gold
    const isAboveNisab = eligibleAssets >= nisab;
    const zakatDue = isAboveNisab ? eligibleAssets * 0.025 : 0;

    setResult({ eligibleAssets, nisab, zakatDue, isAboveNisab });
  };

  const reset = () => {
    setPortfolioValue("");
    setCash("");
    setReceivables("");
    setLiabilities("");
    setResult(null);
  };

  const fmtSAR = (n: number) =>
    n.toLocaleString(locale === "ar" ? "ar-SA" : "en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });

  return (
    <section className="py-20 bg-gradient-to-b from-white to-emerald-50/30">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-1.5 rounded-full bg-mizan-green/10 text-mizan-green text-sm font-medium mb-4 font-arabic">
            {locale === "ar" ? "🌙 رمضان ومالك" : "🌙 Faith & Finance"}
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
            <div className="space-y-5">
              {/* Portfolio Value */}
              <div>
                <label className="block text-sm font-medium text-mizan-ink mb-2 font-arabic">
                  {t.portfolioValueLabel}
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={portfolioValue}
                    onChange={(e) => setPortfolioValue(e.target.value)}
                    placeholder="0"
                    className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                    dir={locale === "ar" ? "rtl" : "ltr"}
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                    {locale === "ar" ? "ر.س" : "SAR"}
                  </span>
                </div>
              </div>

              {/* Cash */}
              <div>
                <label className="block text-sm font-medium text-mizan-ink mb-2 font-arabic">
                  {t.cashLabel}
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={cash}
                    onChange={(e) => setCash(e.target.value)}
                    placeholder="0"
                    className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                    dir={locale === "ar" ? "rtl" : "ltr"}
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                    {locale === "ar" ? "ر.س" : "SAR"}
                  </span>
                </div>
              </div>

              {/* Receivables */}
              <div>
                <label className="block text-sm font-medium text-mizan-ink mb-2 font-arabic">
                  {t.receivablesLabel}
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={receivables}
                    onChange={(e) => setReceivables(e.target.value)}
                    placeholder="0"
                    className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                    dir={locale === "ar" ? "rtl" : "ltr"}
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                    {locale === "ar" ? "ر.س" : "SAR"}
                  </span>
                </div>
              </div>

              {/* Liabilities */}
              <div>
                <label className="block text-sm font-medium text-mizan-ink mb-2 font-arabic">
                  {t.liabilitiesLabel}
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={liabilities}
                    onChange={(e) => setLiabilities(e.target.value)}
                    placeholder="0"
                    className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                    dir={locale === "ar" ? "rtl" : "ltr"}
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                    {locale === "ar" ? "ر.س" : "SAR"}
                  </span>
                </div>
              </div>

              {/* Gold Price */}
              <div>
                <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                  {t.goldPriceLabel}
                </label>
                <p className="text-xs text-mizan-slate mb-2 font-arabic">{t.goldPriceHint}</p>
                <div className="relative">
                  <input
                    type="number"
                    value={goldPrice}
                    onChange={(e) => setGoldPrice(e.target.value)}
                    placeholder="280"
                    className="w-full px-4 py-3 pr-16 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all text-lg font-arabic"
                    dir={locale === "ar" ? "rtl" : "ltr"}
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-mizan-slate font-medium">
                    {locale === "ar" ? "ر.س/غ" : "SAR/g"}
                  </span>
                </div>
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={calculate}
                  className="flex-1 px-6 py-3.5 bg-mizan-green hover:bg-mizan-green-dark text-white font-semibold rounded-xl transition-colors shadow-sm font-arabic"
                >
                  {t.calculate}
                </button>
                <button
                  onClick={reset}
                  className="px-6 py-3.5 bg-gray-100 hover:bg-gray-200 text-mizan-ink font-medium rounded-xl transition-colors font-arabic"
                >
                  {t.reset}
                </button>
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="space-y-6">
            {result ? (
              <>
                <div
                  className={`rounded-2xl p-8 shadow-lg border-2 ${
                    result.isAboveNisab
                      ? "bg-gradient-to-br from-emerald-50 to-green-50 border-mizan-green/30"
                      : "bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-300/30"
                  }`}
                >
                  <h3 className="text-lg font-semibold text-mizan-ink mb-6 font-arabic">
                    {t.resultTitle}
                  </h3>

                  <div className="space-y-4">
                    {/* Eligible Assets */}
                    <div className="flex items-center justify-between pb-4 border-b border-gray-200/50">
                      <span className="text-mizan-slate font-arabic">{t.eligibleAssets}</span>
                      <span className="text-xl font-bold text-mizan-ink">
                        {fmtSAR(result.eligibleAssets)} {locale === "ar" ? "ر.س" : "SAR"}
                      </span>
                    </div>

                    {/* Nisab */}
                    <div className="flex items-center justify-between pb-4 border-b border-gray-200/50">
                      <span className="text-mizan-slate font-arabic">{t.nisabThreshold}</span>
                      <span className="text-xl font-bold text-mizan-ink">
                        {fmtSAR(result.nisab)} {locale === "ar" ? "ر.س" : "SAR"}
                      </span>
                    </div>

                    {/* Status Badge */}
                    <div className="py-2">
                      {result.isAboveNisab ? (
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-mizan-green/10 text-mizan-green text-sm font-medium">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="font-arabic">{t.aboveNisab}</span>
                        </div>
                      ) : (
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-100 text-amber-700 text-sm font-medium">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.707-4.293a1 1 0 00-1.414-1.414L7 11.586 5.707 10.293a1 1 0 10-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="font-arabic">{t.belowNisab}</span>
                        </div>
                      )}
                    </div>

                    {/* Zakat Due */}
                    {result.isAboveNisab && (
                      <div className="bg-mizan-green rounded-xl p-5 text-white">
                        <p className="text-sm opacity-90 font-arabic mb-1">{t.zakatAmount}</p>
                        <div className="flex items-baseline gap-2">
                          <span className="text-3xl font-bold">{fmtSAR(result.zakatDue)}</span>
                          <span className="text-lg opacity-90">{locale === "ar" ? "ر.س" : "SAR"}</span>
                        </div>
                        <p className="text-xs opacity-75 mt-2 font-arabic">{t.zakatRate}</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 p-8 flex items-center justify-center min-h-[300px]">
                <p className="text-mizan-slate text-center font-arabic">
                  {locale === "ar"
                    ? "أدخل قيم أصولك واضغط على زر الحساب لعرض النتيجة"
                    : "Enter your asset values and click calculate to see the result"}
                </p>
              </div>
            )}

            {/* Rules */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h4 className="font-semibold text-mizan-ink mb-4 font-arabic">{t.rulesTitle}</h4>
              <ul className="space-y-3">
                {t.rules.map((rule, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-mizan-green/10 text-mizan-green text-xs font-bold flex items-center justify-center mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-sm text-mizan-slate font-arabic">{rule}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Disclaimer */}
            <p className="text-xs text-mizan-slate/70 text-center font-arabic leading-relaxed">
              ⚠️ {t.disclaimer}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
