"use client";

import { useState } from "react";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";
import type { Locale } from "@/i18n";

interface SettingsProps {
  dict: Dict;
  locale: Locale;
}

export default function SettingsPage({ dict, locale }: SettingsProps) {
  const s = dict.settings;
  const [lang, setLang] = useState(locale);
  const [currency, setCurrency] = useState("SAR");
  const [emailAlerts, setEmailAlerts] = useState(false);
  const [priceAlerts, setPriceAlerts] = useState(false);
  const [weeklyReport, setWeeklyReport] = useState(false);
  const [analytics, setAnalytics] = useState(true);
  const [saved, setSaved] = useState(false);
  const [cleared, setCleared] = useState(false);

  const save = () => {
    const prefs = { lang, currency, emailAlerts, priceAlerts, weeklyReport, analytics };
    localStorage.setItem("mizan_prefs", JSON.stringify(prefs));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const clearData = () => {
    if (confirm(s.clearDataConfirm)) {
      localStorage.removeItem("mizan_watchlist");
      localStorage.removeItem("mizan_prefs");
      localStorage.removeItem("mizan_portfolio");
      setCleared(true);
      setTimeout(() => setCleared(false), 3000);
    }
  };

  const Toggle = ({ enabled, onClick }: { enabled: boolean; onClick: () => void }) => (
    <button
      onClick={onClick}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${enabled ? "bg-emerald-600" : "bg-gray-700"}`}
    >
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${enabled ? "translate-x-6" : "translate-x-1"}`} />
    </button>
  );

  return (
    <section className="py-20 bg-gradient-to-b from-gray-950 to-gray-900 min-h-screen">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-3">{s.title}</h2>
          <p className="text-gray-400 text-lg">{s.subtitle}</p>
        </div>

        {/* Saved toast */}
        {saved && (
          <div className="fixed top-20 right-4 bg-emerald-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-bounce">
            ✓ {s.saved}
          </div>
        )}
        {cleared && (
          <div className="fixed top-20 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50">
            ✓ {s.cleared}
          </div>
        )}

        {/* Language */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6 mb-6">
          <h3 className="text-emerald-400 font-semibold mb-4 text-sm uppercase tracking-wider">{s.languageTitle}</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-gray-400 text-sm mb-2">{s.languageLabel}</label>
              <div className="flex gap-3">
                <button
                  onClick={() => setLang("ar")}
                  className={`px-6 py-2.5 rounded-lg font-medium transition ${lang === "ar" ? "bg-emerald-600 text-white" : "bg-gray-800 text-gray-400 border border-gray-700"}`}
                >
                  {s.arabic}
                </button>
                <button
                  onClick={() => setLang("en")}
                  className={`px-6 py-2.5 rounded-lg font-medium transition ${lang === "en" ? "bg-emerald-600 text-white" : "bg-gray-800 text-gray-400 border border-gray-700"}`}
                >
                  {s.english}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-2">{s.currencyLabel}</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none"
              >
                <option value="SAR">SAR — ريال سعودي</option>
                <option value="USD">USD — US Dollar</option>
                <option value="AED">AED — درهم إماراتي</option>
                <option value="KWD">KWD — دينار كويتي</option>
              </select>
              <p className="text-gray-600 text-xs mt-1">{s.currencyHint}</p>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6 mb-6">
          <h3 className="text-emerald-400 font-semibold mb-4 text-sm uppercase tracking-wider">{s.notificationsTitle}</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm font-medium">{s.emailAlerts}</p>
                <p className="text-gray-500 text-xs">{s.emailAlertsHint}</p>
              </div>
              <Toggle enabled={emailAlerts} onClick={() => setEmailAlerts(!emailAlerts)} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm font-medium">{s.priceAlerts}</p>
                <p className="text-gray-500 text-xs">{s.priceAlertsHint}</p>
              </div>
              <Toggle enabled={priceAlerts} onClick={() => setPriceAlerts(!priceAlerts)} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm font-medium">{s.weeklyReport}</p>
                <p className="text-gray-500 text-xs">{s.weeklyReportHint}</p>
              </div>
              <Toggle enabled={weeklyReport} onClick={() => setWeeklyReport(!weeklyReport)} />
            </div>
          </div>
        </div>

        {/* Privacy */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6 mb-6">
          <h3 className="text-emerald-400 font-semibold mb-4 text-sm uppercase tracking-wider">{s.privacyTitle}</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">{s.analyticsLabel}</p>
              <p className="text-gray-500 text-xs">{s.analyticsHint}</p>
            </div>
            <Toggle enabled={analytics} onClick={() => setAnalytics(!analytics)} />
          </div>
        </div>

        {/* Account */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6 mb-6">
          <h3 className="text-emerald-400 font-semibold mb-4 text-sm uppercase tracking-wider">{s.accountTitle}</h3>
          <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
            <p className="text-gray-400 text-sm">{s.accountHint}</p>
            <Link href={`/${locale}/login`} className="inline-block mt-3 text-emerald-400 hover:text-emerald-300 text-sm font-medium">
              {s.loginPrompt} →
            </Link>
          </div>
          <div className="border-t border-gray-800 pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-400 text-sm font-medium">{s.clearData}</p>
                <p className="text-gray-500 text-xs">{s.clearDataHint}</p>
              </div>
              <button
                onClick={clearData}
                className="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 px-4 py-2 rounded-lg text-sm font-medium transition"
              >
                {s.clearData}
              </button>
            </div>
          </div>
        </div>

        {/* Save button */}
        <button
          onClick={save}
          className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3.5 rounded-xl font-semibold transition"
        >
          {s.saveChanges}
        </button>
      </div>
    </section>
  );
}
