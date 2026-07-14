"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Dict } from "@/i18n/ar";
import { useLocaleAttrs } from "@/i18n/useLocaleAttrs";
import { getDirection } from "@/i18n";
import { useAuth } from "@/contexts/AuthContext";
import type { ApiError } from "@/lib/api";

interface AuthPageProps {
  dict: Dict;
  locale: string;
  mode: "login" | "signup";
}

export default function AuthPage({ dict, locale, mode }: AuthPageProps) {
  const t = dict.auth;
  const dir = getDirection(locale);
  useLocaleAttrs(locale, dir);
  const router = useRouter();
  const { login, register, loginWithToken } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string>("");

  // ── Handle OAuth redirect back (token in URL) ─────────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const oauthError = params.get("error");

    if (token) {
      loginWithToken(token);
      // Clean URL
      window.history.replaceState({}, "", window.location.pathname);
      router.push(`/${locale}`);
      return;
    }

    if (oauthError) {
      const messages: Record<string, string> = {
        access_denied: locale === "ar" ? "تم رفض الوصول" : "Access denied",
        not_configured: locale === "ar" ? "لم يتم إعداد تسجيل الدخول عبر Google" : "Google login not configured",
        invalid_state: locale === "ar" ? "انتهت الجلسة، حاول مرة أخرى" : "Session expired, try again",
        token_exchange_failed: locale === "ar" ? "فشل الاتصال بخدمة Google" : "Failed to connect to Google",
        userinfo_failed: locale === "ar" ? "فشل في الحصول على معلومات المستخدم" : "Failed to get user info",
      };
      setApiError(messages[oauthError] || oauthError);
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [locale, router, loginWithToken]);

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

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    setApiError("");

    if (!validate()) return;

    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register({
          email,
          password,
          full_name: fullName || undefined,
          phone: phone || undefined,
        });
      }
      // Redirect to home on success
      router.push(`/${locale}`);
    } catch (err) {
      const apiErr = err as ApiError;
      setApiError(apiErr.detail || (locale === "ar" ? "حدث خطأ" : "An error occurred"));
    } finally {
      setLoading(false);
    }
  };

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

          {/* Social auth — Google Sign-In */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <a
              href={`/api/auth/google`}
              className="flex items-center justify-center gap-2 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all text-sm font-medium text-mizan-slate"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              {t.googleButton}
            </a>
            <button
              type="button"
              className="flex items-center justify-center gap-2 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium text-mizan-slate cursor-not-allowed opacity-60"
              title={locale === "ar" ? "قريباً" : "Coming soon"}
            >
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

          {/* API Error Banner */}
          {apiError && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700 font-arabic">
              {apiError}
            </div>
          )}

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
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20 outline-none transition-all font-arabic"
                    dir="ltr"
                  />
                </div>
              </>
            )}

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                {t.email || (locale === "ar" ? "البريد الإلكتروني" : "Email")}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors((p) => ({ ...p, email: "" }));
                }}
                className={`w-full px-4 py-3 rounded-xl border outline-none transition-all font-arabic ${
                  errors.email
                    ? "border-red-300 focus:ring-2 focus:ring-red/20"
                    : "border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20"
                }`}
                dir="ltr"
                disabled={loading}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-600 font-arabic">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                {t.password || (locale === "ar" ? "كلمة المرور" : "Password")}
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors((p) => ({ ...p, password: "" }));
                }}
                className={`w-full px-4 py-3 rounded-xl border outline-none transition-all font-arabic ${
                  errors.password
                    ? "border-red-300 focus:ring-2 focus:ring-red/20"
                    : "border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20"
                }`}
                dir="ltr"
                disabled={loading}
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-600 font-arabic">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password (signup only) */}
            {isSignup && (
              <div>
                <label className="block text-sm font-medium text-mizan-ink mb-1.5 font-arabic">
                  {t.confirmPassword || (locale === "ar" ? "تأكيد كلمة المرور" : "Confirm Password")}
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (errors.confirmPassword) setErrors((p) => ({ ...p, confirmPassword: "" }));
                  }}
                  className={`w-full px-4 py-3 rounded-xl border outline-none transition-all font-arabic ${
                    errors.confirmPassword
                      ? "border-red-300 focus:ring-2 focus:ring-red/20"
                      : "border-gray-200 focus:border-mizan-green focus:ring-2 focus:ring-mizan-green/20"
                  }`}
                  dir="ltr"
                  disabled={loading}
                />
                {errors.confirmPassword && (
                  <p className="mt-1 text-xs text-red-600 font-arabic">{errors.confirmPassword}</p>
                )}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-mizan-green hover:bg-mizan-green-dark text-white font-semibold rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-arabic flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {locale === "ar" ? "جاري المعالجة..." : "Processing..."}
                </>
              ) : isSignup ? (
                t.signupButton || (locale === "ar" ? "إنشاء الحساب" : "Create Account")
              ) : (
                t.loginButton || (locale === "ar" ? "تسجيل الدخول" : "Sign In")
              )}
            </button>
          </form>

          {/* Switch link */}
          <p className="text-center mt-6 text-sm text-mizan-slate font-arabic">
            {isSignup
              ? (locale === "ar" ? "لديك حساب بالفعل؟ " : "Already have an account? ")
              : (locale === "ar" ? "ليس لديك حساب؟ " : "Don't have an account? ")}
            <Link
              href={`/${locale}/${isSignup ? "login" : "signup"}`}
              className="text-mizan-green font-semibold hover:underline"
            >
              {isSignup
                ? (locale === "ar" ? "سجل الدخول" : "Sign in")
                : (locale === "ar" ? "أنشئ حساباً" : "Sign up")}
            </Link>
          </p>
        </div>

        {/* Back to home */}
        <div className="text-center mt-4">
          <Link
            href={`/${locale}`}
            className="text-sm text-mizan-slate hover:text-mizan-green transition-colors font-arabic"
          >
            {locale === "ar" ? "← العودة للرئيسية" : "← Back to Home"}
          </Link>
        </div>
      </div>
    </div>
  );
}
