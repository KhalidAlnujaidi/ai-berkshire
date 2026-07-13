/**
 * Centralized API client for the Mizan backend.
 * Handles auth headers, error parsing, and base URL.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "mizan:token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export interface ApiError {
  detail: string;
  status: number;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = "Something went wrong";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON
    }
    const error: ApiError = { detail, status: res.status };
    throw error;
  }

  // 204 No Content or empty body
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Auth API ────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  phone: string | null;
  created_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name?: string;
    phone?: string;
  }) =>
    apiFetch<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    apiFetch<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: () => apiFetch<User>("/api/auth/me"),
};

// ── Watchlist API ───────────────────────────────────────────────────────────

export interface WatchlistItemApi {
  id: number;
  ticker: string;
  name_en: string | null;
  name_ar: string | null;
  sector_en: string | null;
  sector_ar: string | null;
  verdict: string | null;
  added_at: string | null;
}

export const watchlistApi = {
  list: () => apiFetch<WatchlistItemApi[]>("/api/watchlist"),

  add: (data: {
    ticker: string;
    name_en?: string;
    name_ar?: string;
    sector_en?: string;
    sector_ar?: string;
    verdict?: string;
  }) =>
    apiFetch<WatchlistItemApi>("/api/watchlist", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  remove: (ticker: string) =>
    apiFetch<{ status: string; ticker: string }>(
      `/api/watchlist/${encodeURIComponent(ticker)}`,
      { method: "DELETE" }
    ),
};

// ── Research API ────────────────────────────────────────────────────────────

export interface ResearchJobResponse {
  job_id: number;
  ticker: string;
  status: string;
}

export interface ResearchReport {
  id: number;
  ticker: string;
  company_name: string | null;
  status: string;
  rating: string | null;
  summary: string | null;
  report_markdown: string | null;
  error: string | null;
  is_sample: boolean;
  created_at: string | null;
  completed_at: string | null;
}

export interface ResearchListItem {
  id: number;
  ticker: string;
  company_name: string | null;
  status: string;
  rating: string | null;
  summary: string | null;
  is_sample: boolean;
  created_at: string | null;
  completed_at: string | null;
}

export const researchApi = {
  start: (ticker: string) =>
    apiFetch<ResearchJobResponse>("/api/research", {
      method: "POST",
      body: JSON.stringify({ ticker }),
    }),

  get: (jobId: number) =>
    apiFetch<ResearchReport>(`/api/research/${jobId}`),

  history: (limit = 20, offset = 0) =>
    apiFetch<ResearchListItem[]>(
      `/api/research/history?limit=${limit}&offset=${offset}`
    ),

  samples: () => apiFetch<ResearchReport[]>("/api/research/samples"),

  /** SSE stream URL for agent pipeline progress */
  streamUrl: (jobId: number) => `${API_BASE}/api/reports/${jobId}/stream`,
};

export interface SearchResult {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
  verdict: string;
  verdict_ar: string;
}

export const searchApi = {
  search: (q: string) =>
    apiFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}`),
};

export interface AgentStep {
  agent: string;
  status: "running" | "done" | "error";
  summary: string;
  started_at?: number;
  completed_at?: number;
}

export interface AgentProgressData {
  status: "running" | "complete";
  agents: AgentStep[];
}

// ── Billing API ─────────────────────────────────────────────────────────────

export interface SubscriptionInfo {
  is_subscribed: boolean;
  plan: string | null;
  status: string | null;
  current_period_end: string | null;
}

export const billingApi = {
  getSubscription: () =>
    apiFetch<SubscriptionInfo>("/api/billing/subscription"),

  createCheckout: (plan: string) =>
    apiFetch<{ url: string }>("/api/billing/create-checkout-session", {
      method: "POST",
      body: JSON.stringify({ plan }),
    }),

  createPortal: () =>
    apiFetch<{ url: string }>("/api/billing/create-portal-session", {
      method: "POST",
    }),
};

export { API_BASE };
