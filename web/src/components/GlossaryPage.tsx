"use client";

import { useState, useMemo } from "react";
import type { Dict } from "@/i18n/ar";
import type { Locale } from "@/i18n";

interface GlossaryProps {
  dict: Dict;
  locale: Locale;
}

const categoryColors: Record<string, string> = {
  sharia: "border-emerald-500/30 bg-emerald-500/5",
  ratios: "border-blue-500/30 bg-blue-500/5",
  investment: "border-amber-500/30 bg-amber-500/5",
  screening: "border-purple-500/30 bg-purple-500/5",
};

const categoryBadgeColors: Record<string, string> = {
  sharia: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  ratios: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  investment: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  screening: "bg-purple-500/15 text-purple-400 border-purple-500/30",
};

export default function GlossaryPage({ dict, locale }: GlossaryProps) {
  const g = dict.glossary;
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("");

  const filtered = useMemo(() => {
    return g.terms.filter((t: { term: string; definition: string; category: string }) => {
      const matchesCategory = !activeCategory || t.category === activeCategory;
      const q = query.toLowerCase();
      const matchesQuery = !q || t.term.toLowerCase().includes(q) || t.definition.toLowerCase().includes(q);
      return matchesCategory && matchesQuery;
    });
  }, [g.terms, query, activeCategory]);

  return (
    <section className="py-20 bg-gradient-to-b from-gray-950 to-gray-900 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-3">{g.title}</h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">{g.subtitle}</p>
        </div>

        {/* Search */}
        <div className="max-w-md mx-auto mb-6">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={g.searchPlaceholder}
              className="w-full bg-gray-800 text-white border border-gray-700 rounded-xl px-12 py-3 text-sm focus:border-emerald-500 focus:outline-none transition"
            />
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Category filters */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          <button
            onClick={() => setActiveCategory("")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              !activeCategory ? "bg-emerald-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {g.allCategories}
          </button>
          {(Object.keys(g.categories) as string[]).map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeCategory === cat ? "bg-emerald-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {g.categories[cat as keyof typeof g.categories]}
            </button>
          ))}
        </div>

        {/* Count */}
        <div className="text-center mb-6">
          <span className="text-gray-500 text-sm">{filtered.length} / {g.terms.length}</span>
        </div>

        {/* Terms grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((t: { term: string; definition: string; category: string }, i: number) => (
            <div
              key={i}
              className={`border rounded-xl p-5 transition hover:scale-[1.02] ${categoryColors[t.category] || "border-gray-700 bg-gray-800/50"}`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <h3 className="text-white font-bold text-lg">{t.term}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full border whitespace-nowrap ${categoryBadgeColors[t.category] || "bg-gray-700 text-gray-400 border-gray-600"}`}>
                  {g.categories[t.category as keyof typeof g.categories] || t.category}
                </span>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed">{t.definition}</p>
            </div>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-20">
            <p className="text-gray-500 text-lg">—</p>
          </div>
        )}
      </div>
    </section>
  );
}
