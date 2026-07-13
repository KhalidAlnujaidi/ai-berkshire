"use client";

import Link from "next/link";
import type { Dict } from "@/i18n/ar";

interface AIResearchPipelineProps {
  dict: Dict;
  locale: string;
}

const AGENTS = [
  { icon: "📈", name: "Market Analyst", nameAr: "محلل السوق", color: "from-blue-500 to-blue-600" },
  { icon: "📊", name: "Fundamentals Analyst", nameAr: "محلل الأساسيات", color: "from-indigo-500 to-indigo-600" },
  { icon: "📰", name: "News Analyst", nameAr: "محلل الأخبار", color: "from-purple-500 to-purple-600" },
  { icon: "🕌", name: "Sharia Analyst", nameAr: "محلل الامتثال الشرعي", color: "from-emerald-500 to-emerald-600" },
  { icon: "👨‍💼", name: "Research Manager", nameAr: "مدير البحث", color: "from-amber-500 to-amber-600" },
  { icon: "🏆", name: "Portfolio Manager", nameAr: "مدير المحفظة", color: "from-mizan-green to-mizan-green-dark" },
];

export default function AIResearchPipeline({ dict, locale }: AIResearchPipelineProps) {
  const isAr = locale === "ar";

  return (
    <section className="py-20 md:py-28 bg-gradient-to-b from-white to-mizan-green-pale/20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Badge */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-mizan-green/10 rounded-full">
            <span className="w-2 h-2 bg-mizan-green rounded-full animate-pulse" />
            <span className="text-sm font-medium text-mizan-green-dark">
              {isAr ? "مدعوم بالذكاء الاصطناعي" : "AI-Powered"}
            </span>
          </div>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-4">
            {isAr ? "فريق استثماري متكامل من الذكاء الاصطناعي" : "A Full Investment Team of AI Agents"}
          </h2>
          <p className="text-lg text-mizan-slate max-w-3xl mx-auto leading-relaxed">
            {isAr
              ? "ليس مجرد تقرير — بل فريق كامل من وكلاء الذكاء الاصطناعي المتخصصين يحللون السهم من كل زاوية: السوق، الأساسيات، الأخبار، الامتثال الشرعي، والمخاطر."
              : "Not just a report — a full team of specialized AI agents analyzing every angle: market, fundamentals, news, Sharia compliance, and risk — all in parallel."}
          </p>
        </div>

        {/* Pipeline flow */}
        <div className="relative mb-16">
          {/* Connecting line */}
          <div className="hidden md:block absolute top-1/2 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-blue-200 via-mizan-green/30 to-mizan-green" />

          {/* Agent cards grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6">
            {AGENTS.map((agent, i) => (
              <div key={agent.name} className="group relative">
                <div className="bg-white rounded-2xl border border-gray-100 hover:border-mizan-green/30 hover:shadow-lg transition-all duration-300 p-5 text-center">
                  {/* Icon */}
                  <div className={`w-14 h-14 mx-auto mb-3 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center text-2xl shadow-md group-hover:scale-110 transition-transform duration-300`}>
                    {agent.icon}
                  </div>

                  {/* Name */}
                  <h3 className="text-sm font-bold text-mizan-ink mb-1">
                    {isAr ? agent.nameAr : agent.name}
                  </h3>

                  {/* Arrow (desktop only) */}
                  {i < AGENTS.length - 1 && (
                    <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                      <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Features grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {/* Parallel analysis */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center mb-4">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-mizan-ink mb-2">
              {isAr ? "تحليل متوازي" : "Parallel Analysis"}
            </h3>
            <p className="text-sm text-mizan-slate leading-relaxed">
              {isAr
                ? "جميع المحللين يعملون في وقت واحد — ليس بالتسلسل. تحصل على التقرير الكامل في أقل من دقيقتين."
                : "All analysts work simultaneously, not sequentially. Get a complete report in under 2 minutes."}
            </p>
          </div>

          {/* Sharia-first */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center mb-4">
              <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-mizan-ink mb-2">
              {isAr ? "الامتثال الشرعي أولاً" : "Sharia-First"}
            </h3>
            <p className="text-sm text-mizan-slate leading-relaxed">
              {isAr
                ? "محلل شرعي مخصص يفحص كل سهم وفق معيار AAOIFI رقم 21. إذا كان السهم غير متوافق، يتم رفضه فوراً — بغض النظر عن جاذبيته المالية."
                : "A dedicated Sharia analyst screens every stock under AAOIFI Standard 21. Non-compliant stocks are hard-failed regardless of financial appeal."}
            </p>
          </div>

          {/* Live streaming */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center mb-4">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-mizan-ink mb-2">
              {isAr ? "بث مباشر للتحليل" : "Live Progress Streaming"}
            </h3>
            <p className="text-sm text-mizan-slate leading-relaxed">
              {isAr
                ? "شاهد وكلاء الذكاء الاصطناعي وهم يعملون في الوقت الفعلي — كل محلل يظهر اسمه وحالته ونتيجته فور اكتماله."
                : "Watch the AI agents work in real-time — each analyst appears with its name, status, and result as it completes."}
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link
            href={`/${locale}/research`}
            className="inline-flex items-center gap-2 px-8 py-4 bg-mizan-green hover:bg-mizan-green-dark text-white font-bold rounded-xl transition-colors shadow-lg shadow-mizan-green/20 text-lg"
          >
            {isAr ? "جرب التحليل الآن" : "Try AI Analysis Now"}
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <p className="text-sm text-mizan-slate mt-3">
            {isAr ? "مجاناً — بدون بطاقة ائتمان" : "Free — No credit card required"}
          </p>
        </div>
      </div>
    </section>
  );
}
