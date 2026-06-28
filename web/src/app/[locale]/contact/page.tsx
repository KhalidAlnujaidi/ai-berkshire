"use client";

import { useState } from "react";
import { getDict, getDirection, type Locale } from "@/i18n";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function ContactPage({ params }: { params: { locale: string } }) {
  const locale = params.locale as Locale;
  const dict = getDict(locale);
  const dir = getDirection(locale);
  useLocaleAttrs(locale, dir);

  const t = dict.contact;
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    // Simulate API call — in production this would POST to /api/contact
    await new Promise((r) => setTimeout(r, 1500));
    setStatus("success");
  };

  return (
    <>
      <Navbar dict={dict} locale={locale} />
      <main className="pt-24 pb-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className={`text-4xl font-bold text-mizan-ink mb-4 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
              {t.title}
            </h1>
            <p className={`text-lg text-mizan-slate ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
              {t.subtitle}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Form */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <h2 className={`text-xl font-semibold text-mizan-ink mb-6 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                {t.formTitle}
              </h2>

              {status === "success" ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 rounded-full bg-mizan-green-pale flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-mizan-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className={`text-mizan-ink ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                    {t.successMessage}
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className={`block text-sm font-medium text-mizan-slate mb-1 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                      {t.nameLabel}
                    </label>
                    <input
                      type="text"
                      required
                      placeholder={t.namePlaceholder}
                      className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-mizan-green focus:ring-1 focus:ring-mizan-green outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium text-mizan-slate mb-1 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                      {t.emailLabel}
                    </label>
                    <input
                      type="email"
                      required
                      placeholder={t.emailPlaceholder}
                      className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-mizan-green focus:ring-1 focus:ring-mizan-green outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium text-mizan-slate mb-1 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                      {t.subjectLabel}
                    </label>
                    <input
                      type="text"
                      required
                      placeholder={t.subjectPlaceholder}
                      className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-mizan-green focus:ring-1 focus:ring-mizan-green outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium text-mizan-slate mb-1 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                      {t.messageLabel}
                    </label>
                    <textarea
                      required
                      rows={4}
                      placeholder={t.messagePlaceholder}
                      className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-mizan-green focus:ring-1 focus:ring-mizan-green outline-none transition-colors resize-none"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={status === "submitting"}
                    className="w-full py-3 bg-mizan-green hover:bg-mizan-green-dark text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
                  >
                    {status === "submitting" ? t.submitting : t.submitButton}
                  </button>
                  {status === "error" && (
                    <p className="text-sm text-red-600 text-center">{t.errorMessage}</p>
                  )}
                </form>
              )}
            </div>

            {/* Direct contact */}
            <div className="space-y-6">
              <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                <h2 className={`text-xl font-semibold text-mizan-ink mb-6 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                  {t.directTitle}
                </h2>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-mizan-green-pale flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-mizan-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <div className={`text-xs text-gray-400 ${locale === "ar" ? "font-arabic" : ""}`}>{t.emailLabel2}</div>
                      <a href={`mailto:${t.emailValue}`} className="text-mizan-green font-medium hover:underline">
                        {t.emailValue}
                      </a>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-mizan-green-pale flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-mizan-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div>
                      <div className={`text-sm text-mizan-slate ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                        {t.responseTime}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-mizan-green-pale flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-mizan-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <div>
                      <div className={`text-xs text-gray-400 ${locale === "ar" ? "font-arabic" : ""}`}>Privacy</div>
                      <a href={`mailto:${t.privacyEmail}`} className="text-mizan-green font-medium hover:underline text-sm">
                        {t.privacyEmail}
                      </a>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-mizan-green-pale flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-mizan-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                      </svg>
                    </div>
                    <div>
                      <div className={`text-xs text-gray-400 ${locale === "ar" ? "font-arabic" : ""}`}>Legal</div>
                      <a href={`mailto:${t.legalEmail}`} className="text-mizan-green font-medium hover:underline text-sm">
                        {t.legalEmail}
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              {/* Social */}
              <div className="bg-gradient-to-br from-mizan-green to-mizan-green-dark rounded-2xl p-8">
                <h3 className={`text-lg font-semibold text-white mb-4 ${locale === "ar" ? "font-arabic" : "font-latin"}`}>
                  {t.socialTitle}
                </h3>
                <div className="flex gap-3">
                  <a href="#" className="w-10 h-10 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
                  </a>
                  <a href="#" className="w-10 h-10 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.04c-5.5 0-10 4.49-10 10.02 0 5 3.66 9.15 8.44 9.9v-7H7.9v-2.9h2.54V9.85c0-2.51 1.49-3.89 3.78-3.89 1.09 0 2.23.19 2.23.19v2.47h-1.26c-1.24 0-1.63.77-1.63 1.56v1.88h2.78l-.45 2.9h-2.33v7a10 10 0 008.44-9.9c0-5.53-4.5-10.02-10-10.02z" /></svg>
                  </a>
                  <a href="#" className="w-10 h-10 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 1.366.062 2.633.334 3.608 1.31.975.975 1.248 2.242 1.31 3.608.058 1.266.069 1.646.069 4.85s-.011 3.584-.069 4.85c-.062 1.366-.335 2.633-1.31 3.608-.975.975-2.242 1.248-3.608 1.31-1.266.058-1.646.069-4.85.069s-3.584-.011-4.85-.069c-1.366-.062-2.633-.335-3.608-1.31-.975-.975-1.248-2.242-1.31-3.608C2.175 15.747 2.163 15.367 2.163 12s.012-3.584.07-4.85c.062-1.366.334-2.633 1.31-3.608.975-.975 2.242-1.248 3.608-1.31C8.416 2.175 8.796 2.163 12 2.163zm0 1.838c-3.143 0-3.51.012-4.747.068-1.022.047-1.575.217-1.944.36-.49.19-.838.418-1.205.785-.367.367-.595.715-.785 1.205-.143.369-.313.922-.36 1.944-.056 1.237-.068 1.604-.068 4.747s.012 3.51.068 4.747c.047 1.022.217 1.575.36 1.944.19.49.418.838.785 1.205.367.367.715.595 1.205.785.369.143.922.313 1.944.36 1.237.056 1.604.068 4.747.068s3.51-.012 4.747-.068c1.022-.047 1.575-.217 1.944-.36.49-.19.838-.418 1.205-.785.367-.367.595-.715.785-1.205.143-.369.313-.922.36-1.944.056-1.237.068-1.604.068-4.747s-.012-3.51-.068-4.747c-.047-1.022-.217-1.575-.36-1.944-.19-.49-.418-.838-.785-1.205-.367-.367-.715-.595-1.205-.785-.369-.143-.922-.313-1.944-.36C15.51 4.013 15.143 4 12 4zm0 3.838a4.16 4.16 0 100 8.32 4.16 4.16 0 000-8.32zm0 6.857a2.697 2.697 0 110-5.394 2.697 2.697 0 010 5.394zm5.287-7.047a.973.973 0 11-1.946 0 .973.973 0 011.946 0z" /></svg>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer dict={dict} locale={locale} />
    </>
  );
}
