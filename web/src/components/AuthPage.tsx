"use client";

import { useState } from "react";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import { getDirection } from "@/i18n";

interface AuthPageProps {
  dict: Dict;
  locale: string;
  mode: "login" | "signup";
}

export default function AuthPage({ dict, locale, mode }: AuthPageProps) {
  const t = dict.auth;
  const dir = getDirection(locale);
  useLocaleAttrs(locale, dir);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      e.email = t.invalidEmail;
    }
    if (!password || password.length < 8) {
      e.password = t.passwordTooShort;
    }
    if (mode === "signup") {
      if (confirmPassword !== password) {
        e.confirmPassword = t.passwordMismatch;
      }
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = (ev: React.FormEvent) => {
    ev.preventDefault();
    if (validate()) {
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-mizan-green-pale via-white to-amber-50/30 px-4">
        <div className="max-w-md w-full text-center">
          <div className="w-20 h-20 rounded-full bg-mizan-green/10 flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-mizan-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-mizan-ink mb-3 font-arabic">
            {mode === "login" ? t.welcomeBack : t.accountCreated}
          </h2>
          <p className="text-mizan-slate mb-8 font-arabic">{t.comingSoon}</p>

          {/* Features preview */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 text-start">
            <p className="text-sm font-medium text-mizan-ink mb-4 font-arabic">{t.betaNotice}</p>
            <ul className="space-y-3">
              {t.featuresPreview.map((f, i) => (
                <li key={i} className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-mizan-green flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-mizan-slate font-arabic">{f}</span>
                </li>
              ))}
            </ul>
          </div>

          <Link
            href={`/${locale}`}
            className="inline-block mt-6 px-6 py-3 bg-mizan-green hover:bg-mizan-green-dark text-white font-semibold rounded-xl transition-colors font-arabic"
          >
            {locale === "ar" ? "العودة للرئيسية" : "Back to Home"}
          </Link>
        </div>
      </div>
    );
  }

  const isSignup = mode === "signup";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-mizan-green-pale via-white to-amber-50/20 px-4 py-12">
      <div className="max-w-md w-full">
        {/* Logo */}
        <Link href={`/${locale}`} className="flex items-center justify-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mizan-green to-mizan-green-dark flex items-center justify-center shadow-md">
            <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 text-white">
              <path d="M12 3v18M5 8h14M7 8l-2 6a4 4 0 008 0L11 8M13 8l-2 6a4 4 0 008 0L17 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="text-xl font-bold text-mizan-ink font-arabic">
            {locale === "ar" ? "ميزان" : "Mizan"}
          </span>
        </Link>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <h1 className="text-2xl font-bold text-mizan-ink mb-2 font-arabic">
            {isSignup ? t.signupTitle : t.loginTitle}
          </h1>
          <p className="text-sm text-mizan-slate mb-6 font-arabic">
            {isSignup ? t.signupSubtitle : t.loginSubtitle}
          </p>

          {/* Social auth */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <button className="flex items-center justify-center gap-2 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium text-mizan-slate">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              {t.googleButton}
            </button>
            <button className="flex items-center justify-center gap-2 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium text-mizan-slate">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
              </svg>
              {t.appleButton}
            </button>
          </div>

          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-mizan-slate font-arabic">{t.orContinueWith}</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <>
                <div>
                  <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                    {t.fullName}
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all font-arabic"
                    dir={dir}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                    {t.phone}
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="05xxxxxxxx"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all font-arabic"
                    dir="ltr"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                {t.email}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full px-4 py-3 rounded-xl border outline-none transition-all font-arabic ${
                  errors.email
                    ? "border-red-300 focus:ring-2 focus:ring-red-200"
                    : "border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20"
                }`}
                dir="ltr"
              />
              {errors.email && (
                <p className="text-xs text-red-500 mt-1 font-arabic">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                {t.password}
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full px-4 py-3 rounded-xl border outline-none transition-all font-arabic ${
                  errors.password
                    ? "border-red-300 focus:ring-2 focus:ring-red-200"
                    : "border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20"
                }`}
                dir="ltr"
              />
              {errors.password && (
                <p className="text-xs text-red-500 mt-1 font-arabic">{errors.password}</p>
              )}
            </div>

            {isSignup && (
              <div>
                <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                  {t.confirmPassword}
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={`w-full px-4 py-3 rounded-xl border outline-none transition-all font-arabic ${
                    errors.confirmPassword
                      ? "border-red-300 focus:ring-2 focus:ring-red-200"
                      : "border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20"
                  }`}
                  dir="ltr"
                />
                {errors.confirmPassword && (
                  <p className="text-xs text-red-500 mt-1 font-arabic">{errors.confirmPassword}</p>
                )}
              </div>
            )}

            {!isSignup && (
              <div className="text-end">
                <Link href="#" className="text-sm text-mizan-green hover:underline font-arabic">
                  {t.forgotPassword}
                </Link>
              </div>
            )}

            <button
              type="submit"
              className="w-full py-3.5 bg-mizan-green hover:bg-mizan-green-dark text-white font-semibold rounded-xl transition-colors shadow-sm font-arabic"
            >
              {isSignup ? t.signupButton : t.loginButton}
            </button>
          </form>

          {/* Terms */}
          {isSignup && (
            <p className="text-xs text-center text-mizan-slate mt-6 font-arabic">
              {t.agreeToTerms}{" "}
              <Link href={`/${locale}/terms`} className="text-mizan-green hover:underline">
                {t.termsLink}
              </Link>{" "}
              {t.and}{" "}
              <Link href={`/${locale}/privacy`} className="text-mizan-green hover:underline">
                {t.privacyLink}
              </Link>
            </p>
          )}

          {/* Switch */}
          <p className="text-sm text-center text-mizan-slate mt-6 font-arabic">
            {isSignup ? t.haveAccount : t.noAccount}{" "}
            <Link
              href={`/${locale}/${isSignup ? "login" : "signup"}`}
              className="text-mizan-green font-medium hover:underline"
            >
              {isSignup ? t.loginInstead : t.createAccount}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
