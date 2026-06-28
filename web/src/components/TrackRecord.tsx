"use client";

import type { Dict } from "@/i18n/ar";

interface TrackRecordProps {
  dict: Dict;
}

export default function TrackRecord({ dict }: TrackRecordProps) {
  const t = dict.trackRecord;

  return (
    <section id="track-record" className="py-20 md:py-28 bg-mizan-ink text-white relative overflow-hidden">
      {/* Background accents */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/4 right-0 w-[400px] h-[400px] bg-mizan-green/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 left-1/4 w-[300px] h-[300px] bg-mizan-gold/8 rounded-full blur-[80px]" />
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-mizan-green/15 border border-mizan-green/30 text-mizan-green text-sm font-medium mb-6 font-arabic">
            {t.badge}
          </div>
          <h2 className="text-3xl md:text-5xl font-bold mb-4 font-arabic">
            {t.title}
          </h2>
          <p className="text-lg text-gray-300 max-w-3xl mx-auto font-arabic">
            {t.subtitle}
          </p>
        </div>

        {/* Returns — headline numbers */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center backdrop-blur-sm">
            <div className="text-sm text-gray-400 mb-2 font-arabic">{t.year2024}</div>
            <div className="text-5xl md:text-6xl font-bold text-mizan-green font-arabic">
              +69.29%
            </div>
            <div className="text-sm text-gray-400 mt-2 font-arabic">{t["beatS&P"]}: 46pp</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center backdrop-blur-sm">
            <div className="text-sm text-gray-400 mb-2 font-arabic">{t.year2025}</div>
            <div className="text-5xl md:text-6xl font-bold text-mizan-gold font-arabic">
              +66.38%
            </div>
            <div className="text-sm text-gray-400 mt-2 font-arabic">{t["beatS&P"]}: 50pp</div>
          </div>
        </div>

        {/* Comparison table */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 md:p-8 backdrop-blur-sm">
          <h3 className="text-xl font-semibold mb-6 text-center font-arabic">{t.tableTitle}</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm md:text-base">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-3 px-4 text-gray-400 font-arabic">{t.colStrategy}</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-arabic">{t.col2024}</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-arabic">{t.col2025}</th>
                </tr>
              </thead>
              <tbody>
                {t.rows.map((row, i) => (
                  <tr
                    key={i}
                    className={`border-b border-white/5 ${row.highlight ? "bg-mizan-green/10" : ""}`}
                  >
                    <td className={`py-3 px-4 font-arabic ${row.highlight ? "text-mizan-green font-bold" : "text-gray-200"}`}>
                      {row.name}
                    </td>
                    <td className={`text-right py-3 px-4 font-mono font-arabic ${row.highlight ? "text-mizan-green font-bold" : "text-gray-300"}`}>
                      {row.y2024}
                    </td>
                    <td className={`text-right py-3 px-4 font-mono font-arabic ${row.highlight ? "text-mizan-green font-bold" : "text-gray-300"}`}>
                      {row.y2025}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-center text-xs text-gray-500 mt-8 max-w-2xl mx-auto font-arabic">
          {t.disclaimer}
        </p>
      </div>
    </section>
  );
}
