"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Dict } from "@/i18n/ar";
import { useAuth } from "@/contexts/AuthContext";
import {
  researchApi,
  billingApi,
  type ResearchReport,
  type ResearchListItem,
  type ApiError,
  type AgentStep,
  type AgentProgressData,
} from "@/lib/api";

interface ResearchPageProps {
  dict: Dict;
  locale: string;
}

const POLL_INTERVAL = 3000; // 3s fallback (when SSE fails)

function statusBadge(status: string, dict: Dict) {
  const s = dict.research.status;
  switch (status) {
    case "completed":
      return { cls: "bg-mizan-green/15 text-mizan-green-dark", label: s.completed, icon: "✓" };
    case "pending":
      return { cls: "bg-amber-100 text-amber-700", label: s.pending, icon: "◌" };
    case "running":
      return { cls: "bg-blue-100 text-blue-700", label: s.running, icon: "↻" };
    case "failed":
      return { cls: "bg-red-100 text-red-700", label: s.failed, icon: "✕" };
    default:
      return { cls: "bg-gray-100 text-gray-600", label: status, icon: "" };
  }
}

function ratingColor(rating: string | null) {
  if (!rating) return null;
  const r = rating.toUpperCase();
  if (r.includes("STRONG") && r.includes("BUY")) return "text-mizan-green-dark bg-mizan-green/15";
  if (r.includes("BUY")) return "text-mizan-green bg-mizan-green-pale";
  if (r.includes("HOLD")) return "text-amber-700 bg-amber-100";
  if (r.includes("SELL")) return "text-red-600 bg-red-100";
  if (r.includes("COMPLIANT")) return "text-mizan-green-dark bg-mizan-green/15";
  return "text-mizan-slate bg-gray-100";
}

function fmtDate(iso: string | null, locale: string) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(locale === "ar" ? "ar-SA" : "en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

// ── Agent icon map ──────────────────────────────────────────────────────────

const AGENT_ICONS: Record<string, string> = {
  market_analyst: "📈",
  fundamentals_analyst: "📊",
  news_analyst: "📰",
  sharia_analyst: "🕌",
  analyst_sync: "🔄",
  bull_researcher: "🐂",
  bear_researcher: "🐻",
  research_manager: "👨‍💼",
  trader: "💼",
  aggressive_debator: "🔥",
  conservative_debator: "🛡️",
  neutral_debator: "⚖️",
  portfolio_manager: "🏆",
};

// ── Agent Progress Cards ────────────────────────────────────────────────────

function AgentProgressCards({
  agents,
  dict,
}: {
  agents: AgentStep[];
  dict: Dict;
}) {
  const t = dict.research.progress;
  return (
    <div className="space-y-2">
      {agents.map((step, i) => {
        const name = t.agents[step.agent as keyof typeof t.agents] || step.agent;
        const icon = AGENT_ICONS[step.agent] || "🤖";
        const isRunning = step.status === "running";
        const isDone = step.status === "done";
        const isError = step.status === "error";
        return (
          <div
            key={step.agent + i}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all ${
              isRunning
                ? "bg-blue-50 border-blue-200 shadow-sm"
                : isDone
                ? "bg-mizan-green-pale/50 border-mizan-green/20"
                : isError
                ? "bg-red-50 border-red-200"
                : "bg-gray-50 border-gray-100"
            }`}
          >
            {/* Icon */}
            <div
              className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0 ${
                isRunning
                  ? "bg-blue-100"
                  : isDone
                  ? "bg-mizan-green/10"
                  : isError
                  ? "bg-red-100"
                  : "bg-gray-100"
              }`}
            >
              {isRunning ? (
                <span className="animate-spin inline-block">⟳</span>
              ) : isDone ? (
                <span>✓</span>
              ) : (
                icon
              )}
            </div>

            {/* Name + summary */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-semibold ${
                    isRunning ? "text-blue-700" : isDone ? "text-mizan-green-dark" : "text-mizan-ink"
                  }`}
                >
                  {icon} {name}
                </span>
                {isRunning && (
                  <span className="text-xs text-blue-500 animate-pulse">
                    {t.status_running}
                  </span>
                )}
                {isDone && (
                  <span className="text-xs text-mizan-green-dark">{t.status_done}</span>
                )}
                {isError && (
                  <span className="text-xs text-red-600">{t.status_error}</span>
                )}
              </div>
              {step.summary && (
                <p className="text-xs text-mizan-slate mt-0.5 truncate max-w-md">
                  {step.summary}
                </p>
              )}
            </div>

            {/* Animated bar */}
            {isRunning && (
              <div className="w-16 h-1.5 bg-blue-100 rounded-full overflow-hidden flex-shrink-0">
                <div className="h-full bg-blue-500 rounded-full animate-progress-pulse" />
              </div>
            )}
            {isDone && (
              <div className="w-16 h-1.5 bg-mizan-green/10 rounded-full overflow-hidden flex-shrink-0">
                <div className="h-full w-full bg-mizan-green rounded-full" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────────

export default function ResearchPage({ dict, locale }: ResearchPageProps) {
  const t = dict.research;
  const { user, loading: authLoading, isAuthenticated } = useAuth();

  const [ticker, setTicker] = useState("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [activeJobId, setActiveJobId] = useState<number | null>(null);
  const [activeReport, setActiveReport] = useState<ResearchReport | null>(null);
  const [agentProgress, setAgentProgress] = useState<AgentStep[]>([]);
  const [history, setHistory] = useState<ResearchListItem[]>([]);
  const [samples, setSamples] = useState<ResearchReport[]>([]);
  const [subscribed, setSubscribed] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, []);

  // Fetch samples
  useEffect(() => {
    researchApi.samples().then(setSamples).catch(() => {});
  }, []);

  // Check subscription + fetch history
  useEffect(() => {
    if (!isAuthenticated) return;
    billingApi.getSubscription().then((info) => setSubscribed(info.is_subscribed)).catch(() => {});
    setLoadingHistory(true);
    researchApi.history().then(setHistory).catch(() => {}).finally(() => setLoadingHistory(false));
  }, [isAuthenticated]);

  // ── SSE stream for progress + fallback polling ─────────────────────
  useEffect(() => {
    if (activeJobId === null) return;

    // Cleanup previous
    if (eventSourceRef.current) eventSourceRef.current.close();
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }

    setAgentProgress([]);

    // Try SSE
    const url = researchApi.streamUrl(activeJobId);
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener("progress", (e: MessageEvent) => {
      try {
        const data: AgentProgressData = JSON.parse(e.data);
        setAgentProgress(data.agents);
        if (data.status === "complete") {
          es.close();
          eventSourceRef.current = null;
        }
      } catch { /* ignore parse errors */ }
    });

    es.addEventListener("complete", () => {
      es.close();
      eventSourceRef.current = null;
    });

    es.onerror = () => {
      // SSE failed — fall back to polling
      es.close();
      eventSourceRef.current = null;

      const poll = async () => {
        try {
          const report = await researchApi.get(activeJobId);
          setActiveReport(report);
          if (report.status === "completed" || report.status === "failed") {
            if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
            setGenerating(false);
            if (report.status === "completed" && isAuthenticated) {
              researchApi.history().then(setHistory).catch(() => {});
            }
          }
        } catch { /* keep polling */ }
      };

      poll();
      pollRef.current = setInterval(poll, POLL_INTERVAL);
    };

    return () => {
      es.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [activeJobId, isAuthenticated]);

  // ── Poll for completion (also runs when SSE completes) ─────────────
  useEffect(() => {
    if (activeJobId === null) return;
    // The SSE handler above sets generating=false on complete
    // But we also need to fetch the final report once
    const check = async () => {
      try {
        const report = await researchApi.get(activeJobId);
        setActiveReport(report);
        if (report.status === "completed" || report.status === "failed") {
          setGenerating(false);
        }
      } catch { /* ignore */ }
    };
    // Check after a delay in case SSE fires but report hasn't been saved yet
    const timer = setTimeout(check, 2000);
    return () => clearTimeout(timer);
  }, [agentProgress]); // re-check whenever progress updates

  const handleGenerate = useCallback(async () => {
    const tk = ticker.trim();
    if (!tk) return;
    setGenerating(true);
    setError("");
    setActiveReport(null);
    setAgentProgress([]);
    try {
      const job = await researchApi.start(tk);
      setActiveJobId(job.job_id);
      setActiveReport(null);
    } catch (e) {
      const err = e as ApiError;
      if (err.status === 402) {
        setError(t.needsSubscriptionDesc);
      } else if (err.status === 429) {
        setError(t.dailyLimit);
      } else {
        setError(err.detail || t.errorOccurred);
      }
      setGenerating(false);
    }
  }, [ticker, t, isAuthenticated]);

  const openReport = useCallback(async (id: number) => {
    setError("");
    setActiveJobId(null);
    if (eventSourceRef.current) { eventSourceRef.current.close(); eventSourceRef.current = null; }
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    setAgentProgress([]);
    try {
      const report = await researchApi.get(id);
      setActiveReport(report);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setError(t.errorOccurred);
    }
  }, [t]);

  // ── Auth gate ────────────────────────────────────────────────────────────
  if (authLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-3 border-mizan-green border-t-transparent rounded-full" />
      </div>
    );
  }

  const showAuthGate = !isAuthenticated;

  return (
    <section className="py-20 md:py-28 bg-gradient-to-b from-mizan-green-pale/20 to-white min-h-screen">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-mizan-green/10 rounded-full mb-4">
            <span className="text-sm font-medium text-mizan-green-dark font-arabic">
              {t.badge}
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-mizan-ink mb-3 font-arabic">
            {t.title}
          </h1>
          <p className="text-mizan-slate max-w-2xl mx-auto font-arabic">
            {t.subtitle}
          </p>
        </div>

        {/* ── Auth gate ── */}
        {showAuthGate ? (
          <div className="max-w-md mx-auto bg-white rounded-2xl shadow-lg border border-mizan-green/10 p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-mizan-green-pale flex items-center justify-center">
              <svg className="w-8 h-8 text-mizan-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-mizan-ink mb-2 font-arabic">
              {t.needsAuth}
            </h3>
            <p className="text-mizan-slate mb-6 font-arabic">{t.needsAuthDesc}</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href={`/${locale}/login`}
                className="px-6 py-3 text-sm font-semibold text-mizan-green border border-mizan-green rounded-xl hover:bg-mizan-green-pale transition-colors font-arabic"
              >
                {t.loginBtn}
              </Link>
              <Link
                href={`/${locale}/signup`}
                className="px-6 py-3 text-sm font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-colors shadow-sm font-arabic"
              >
                {dict.nav.signup}
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* ── Subscription gate ── */}
            {!subscribed && (
              <div className="max-w-2xl mx-auto mb-8 bg-gradient-to-r from-mizan-gold/10 to-amber-50 border border-mizan-gold/30 rounded-2xl p-6 flex flex-col sm:flex-row items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-mizan-gold/20 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-mizan-gold-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                </div>
                <div className="flex-1 text-center sm:text-start">
                  <h3 className="font-bold text-mizan-ink font-arabic">{t.needsSubscription}</h3>
                  <p className="text-sm text-mizan-slate font-arabic">{t.needsSubscriptionDesc}</p>
                </div>
                <a
                  href={`/${locale}#pricing`}
                  className="px-5 py-2.5 text-sm font-semibold text-white bg-mizan-gold hover:bg-mizan-gold-dark rounded-xl transition-colors shadow-sm font-arabic whitespace-nowrap"
                >
                  {t.subscribeBtn}
                </a>
              </div>
            )}

            {/* ── Generator form ── */}
            <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg border border-mizan-green/10 p-6 mb-10">
              <label className="block text-sm font-medium text-mizan-slate mb-2 font-arabic">
                {t.inputLabel}
              </label>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !generating) handleGenerate();
                  }}
                  placeholder={t.inputPlaceholder}
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-mizan-green/30 focus:border-mizan-green transition-all font-arabic"
                  dir="ltr"
                />
                <button
                  onClick={handleGenerate}
                  disabled={generating || !ticker.trim()}
                  className="px-6 py-3 text-sm font-semibold text-white bg-mizan-green hover:bg-mizan-green-dark rounded-xl transition-colors shadow-sm font-arabic disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 justify-center"
                >
                  {generating ? (
                    <>
                      <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                      {t.generating}
                    </>
                  ) : (
                    t.generateBtn
                  )}
                </button>
              </div>
              {error && (
                <div className="mt-3 px-4 py-2.5 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-arabic">
                  {error}
                </div>
              )}
            </div>

            {/* ── Agent progress cards (during generation) ── */}
            {generating && agentProgress.length > 0 && (
              <div className="max-w-2xl mx-auto mb-10">
                <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-6">
                  <h3 className="text-lg font-bold text-mizan-ink mb-1 font-arabic flex items-center gap-2">
                    <span className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
                    {t.progress.title}
                  </h3>
                  <p className="text-sm text-mizan-slate mb-4 font-arabic">
                    {t.progress.subtitle}
                  </p>
                  <AgentProgressCards agents={agentProgress} dict={dict} />
                </div>
              </div>
            )}

            {/* ── Active / generated report ── */}
            {activeReport && (
              <ReportView
                report={activeReport}
                dict={dict}
                locale={locale}
                agentProgress={generating ? agentProgress : []}
                onClose={() => {
                  setActiveReport(null);
                  setActiveJobId(null);
                  setAgentProgress([]);
                }}
              />
            )}

            {/* ── Your reports history ── */}
            <div className="mb-12">
              <h2 className="text-xl font-bold text-mizan-ink mb-4 font-arabic flex items-center gap-2">
                {t.yourReports}
                {!loadingHistory && history.length > 0 && (
                  <span className="text-sm font-normal text-mizan-slate">({history.length})</span>
                )}
              </h2>
              {loadingHistory ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin w-6 h-6 border-2 border-mizan-green border-t-transparent rounded-full" />
                </div>
              ) : history.length === 0 ? (
                <div className="bg-white rounded-xl border border-gray-100 p-8 text-center text-mizan-slate font-arabic">
                  {t.noReports}
                </div>
              ) : (
                <div className="grid gap-3">
                  {history.map((r) => (
                    <ReportCard key={r.id} report={r} dict={dict} locale={locale} onClick={() => openReport(r.id)} />
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* ── Sample reports ── */}
        {samples.length > 0 && (
          <div>
            <h2 className="text-xl font-bold text-mizan-ink mb-4 font-arabic flex items-center gap-2">
              {t.sampleReports}
              <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-mizan-green/10 text-mizan-green-dark rounded-full">
                {locale === "ar" ? "مجاني" : "Free"}
              </span>
            </h2>
            <div className="grid gap-3">
              {samples.map((r) => (
                <ReportCard
                  key={r.id}
                  report={r}
                  dict={dict}
                  locale={locale}
                  onClick={() => openReport(r.id)}
                  isSample
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

// ── Report card ─────────────────────────────────────────────────────────────

function ReportCard({
  report,
  dict,
  locale,
  onClick,
  isSample = false,
}: {
  report: ResearchListItem | ResearchReport;
  dict: Dict;
  locale: string;
  onClick: () => void;
  isSample?: boolean;
}) {
  const t = dict.research;
  const sb = statusBadge(report.status, dict);
  const rc = ratingColor(report.rating);

  return (
    <button
      onClick={onClick}
      disabled={report.status !== "completed"}
      className="w-full text-start bg-white rounded-xl border border-gray-100 hover:border-mizan-green/30 hover:shadow-md transition-all p-4 flex items-center gap-4 group disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-mizan-green-pale flex items-center justify-center">
        <span className="text-lg font-bold text-mizan-green-dark font-latin">
          {report.ticker.slice(0, 4)}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-bold text-mizan-ink font-latin">{report.ticker}</span>
          {report.company_name && (
            <span className="text-sm text-mizan-slate truncate font-arabic">{report.company_name}</span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${sb.cls}`}>
            {sb.icon} {sb.label}
          </span>
          {isSample && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-mizan-green/10 text-mizan-green-dark font-medium">
              {locale === "ar" ? "تجريبي" : "Sample"}
            </span>
          )}
        </div>
        {report.summary && (
          <p className="text-sm text-mizan-slate mt-1 line-clamp-1 font-arabic">{report.summary}</p>
        )}
        {report.created_at && (
          <p className="text-xs text-gray-400 mt-0.5">
            {t.generatedAt}: {fmtDate(report.created_at, locale)}
          </p>
        )}
      </div>
      {rc && report.rating && (
        <div className={`flex-shrink-0 text-xs font-bold px-3 py-1.5 rounded-lg ${rc}`}>
          {report.rating}
        </div>
      )}
      {report.status === "completed" && (
        <svg className="w-5 h-5 text-mizan-green flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      )}
    </button>
  );
}

// ── Full report view ─────────────────────────────────────────────────────────

function ReportView({
  report,
  dict,
  locale,
  agentProgress,
  onClose,
}: {
  report: ResearchReport;
  dict: Dict;
  locale: string;
  agentProgress: AgentStep[];
  onClose: () => void;
}) {
  const t = dict.research;
  const sb = statusBadge(report.status, dict);
  const rc = ratingColor(report.rating);

  return (
    <div className="mb-10 bg-white rounded-2xl shadow-xl border border-mizan-green/10 overflow-hidden animate-fade-in-up">
      {/* Header bar */}
      <div className="bg-gradient-to-r from-mizan-green to-mizan-green-dark px-6 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
            <span className="text-lg font-bold text-white font-latin">{report.ticker.slice(0, 4)}</span>
          </div>
          <div>
            <h3 className="text-xl font-bold text-white font-latin">{report.ticker}</h3>
            {report.company_name && (
              <p className="text-sm text-white/80 font-arabic">{report.company_name}</p>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
          aria-label={t.closeReport}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Status / meta */}
      <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3 flex-wrap">
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${sb.cls}`}>
          {sb.icon} {sb.label}
        </span>
        {report.rating && rc && (
          <span className={`text-xs font-bold px-3 py-1 rounded-lg ${rc}`}>{report.rating}</span>
        )}
        {report.completed_at && (
          <span className="text-xs text-gray-400">
            {t.generatedAt}: {fmtDate(report.completed_at, locale)}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="px-6 py-6">
        {report.status === "pending" || report.status === "running" ? (
          <div className="py-6">
            {agentProgress.length > 0 ? (
              <>
                <h4 className="text-sm font-bold text-mizan-ink mb-3 font-arabic flex items-center gap-2">
                  <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse" />
                  {t.progress.title}
                </h4>
                <AgentProgressCards agents={agentProgress} dict={dict} />
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-8">
                <div className="relative">
                  <div className="animate-spin w-12 h-12 border-3 border-mizan-green border-t-transparent rounded-full" />
                </div>
                <p className="mt-4 text-mizan-slate font-arabic text-center max-w-xs">
                  {t.estimateTime}
                </p>
              </div>
            )}
          </div>
        ) : report.status === "failed" ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700 font-arabic">{report.error || t.errorOccurred}</p>
          </div>
        ) : report.report_markdown ? (
          <>
            {report.summary && (
              <div className="mb-6 p-4 bg-mizan-green-pale rounded-xl border border-mizan-green/15">
                <p className="text-xs font-bold text-mizan-green-dark uppercase tracking-wide mb-1">
                  {t.summaryLabel}
                </p>
                <p className="text-mizan-ink font-arabic">{report.summary}</p>
              </div>
            )}
            <div className="prose prose-mizan max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-2xl font-bold text-mizan-ink mt-6 mb-3">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl font-bold text-mizan-ink mt-5 mb-2 font-arabic">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-semibold text-mizan-ink mt-4 mb-2 font-arabic">{children}</h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-mizan-slate leading-relaxed mb-3 font-arabic">{children}</p>
                  ),
                  ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1 text-mizan-slate font-arabic">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1 text-mizan-slate font-arabic">{children}</ol>,
                  strong: ({ children }) => <strong className="font-bold text-mizan-ink">{children}</strong>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-s-4 border-mizan-green bg-mizan-green-pale/50 ps-4 py-2 my-4 rounded-e-lg">{children}</blockquote>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-4">
                      <table className="w-full border-collapse text-sm">{children}</table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-gray-200 bg-gray-50 px-3 py-2 font-semibold text-mizan-ink text-start">{children}</th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-gray-200 px-3 py-2 text-mizan-slate">{children}</td>
                  ),
                }}
              >
                {report.report_markdown}
              </ReactMarkdown>
            </div>
          </>
        ) : (
          <p className="text-mizan-slate font-arabic">{t.errorOccurred}</p>
        )}
      </div>
    </div>
  );
}