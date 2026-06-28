"use client";

import { useState } from "react";
import type { Dict } from "@/i18n/ar";

interface PricingProps {
  dict: Dict;
}

export default function Pricing({ dict }: PricingProps) {
  const [yearly, setYearly] = useState(false);

  return (
    <section id="pricing" className="py-20 md:py-28 bg-gradient-to-b from-mizan-green-pale/30 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-4 font-arabic">
            {dict.pricing.sectionTitle}
          </h2>
          <p className="text-lg text-mizan-slate font-arabic">{dict.pricing.sectionSubtitle}</p>

          {/* Billing toggle */}
          <div className="inline-flex items-center gap-3 mt-8 bg-gray-100 rounded-full p-1">
            <button
              onClick={() => setYearly(false)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-colors font-arabic ${
                !yearly ? "bg-white text-mizan-ink shadow-sm" : "text-mizan-slate"
              }`}
            >
              {dict.pricing.monthly}
            </button>
            <button
              onClick={() => setYearly(true)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-colors font-arabic flex items-center gap-2 ${
                yearly ? "bg-white text-mizan-ink shadow-sm" : "text-mizan-slate"
              }`}
            >
              {dict.pricing.yearly}
              <span className="text-xs text-mizan-green bg-mizan-green-pale px-2 py-0.5 rounded-full font-arabic">
                {dict.pricing.save}
              </span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 max-w-6xl mx-auto">
          {dict.pricing.plans.map((plan, i) => {
            const displayPrice =
              yearly && plan.price !== "0" && plan.price !== "مخصص" && plan.price !== "Custom"
                ? String(Math.round(Number(plan.price) * 12 * 0.83))
                : plan.price;
            const displayPeriod =
              yearly && plan.price !== "0" && plan.price !== "مخصص" && plan.price !== "Custom"
                ? "/سنوياً"
                : plan.period;

            return (
              <div
                key={i}
                className={`relative rounded-2xl p-8 transition-all duration-300 ${
                  plan.highlight
                    ? "bg-mizan-ink text-white shadow-2xl scale-105 border-2 border-mizan-gold"
                    : "bg-white border border-gray-200 hover:border-mizan-green/30 hover:shadow-lg"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-mizan-gold text-mizan-ink text-xs font-bold rounded-full whitespace-nowrap font-arabic">
                    ★ {dict.pricing.popular}
                  </div>
                )}

                <h3 className={`text-xl font-bold mb-2 font-arabic ${plan.highlight ? "text-white" : "text-mizan-ink"}`}>
                  {plan.name}
                </h3>
                <p className={`text-sm mb-6 font-arabic ${plan.highlight ? "text-gray-300" : "text-mizan-slate"}`}>
                  {plan.description}
                </p>

                <div className="mb-6">
                  <div className="flex items-baseline gap-2">
                    <span className={`text-4xl font-bold font-arabic ${plan.highlight ? "text-mizan-gold" : "text-mizan-green"}`}>
                      {displayPrice}
                    </span>
                    {plan.currency && (
                      <span className={`text-sm font-arabic ${plan.highlight ? "text-gray-300" : "text-mizan-slate"}`}>
                        {plan.currency}
                      </span>
                    )}
                    {displayPeriod && (
                      <span className={`text-sm font-arabic ${plan.highlight ? "text-gray-300" : "text-mizan-slate"}`}>
                        {displayPeriod}
                      </span>
                    )}
                  </div>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, fi) => (
                    <li key={fi} className="flex items-start gap-3">
                      <svg
                        className={`w-5 h-5 flex-shrink-0 mt-0.5 ${plan.highlight ? "text-mizan-gold" : "text-mizan-green"}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className={`text-sm font-arabic ${plan.highlight ? "text-gray-200" : "text-mizan-slate"}`}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-3.5 rounded-xl font-semibold transition-all font-arabic ${
                    plan.highlight
                      ? "bg-mizan-gold text-mizan-ink hover:bg-mizan-gold-light"
                      : "bg-mizan-green-pale text-mizan-green hover:bg-mizan-green hover:text-white"
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
