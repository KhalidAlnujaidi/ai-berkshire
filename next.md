# Mizan — next.md

> Working memory. Keep it short; injected into context.

## Done
- ✅ Backend (FastAPI): 49 Saudi stocks, 14 halal, AAOIFI Standard No. 21
- ✅ Frontend (Next.js 14): Full Arabic/English i18n, RTL, 15+ pages
- ✅ Auth (JWT + bcrypt): register, login, /me, password hashing
- ✅ Database (SQLAlchemy): auto SQLite↔PostgreSQL, User + WatchlistItem models
- ✅ Watchlist: server-synced when authenticated, localStorage fallback
- ✅ Kubernetes (k3s): 5 pods across 4 nodes, ingress, PV, probes, rolling updates

### Production hardening (complete)
- ✅ Rate limiting (slowapi): 5/min register, 10/min login, 3/min reset request
- ✅ Fail-closed JWT guard: app exits if secret <32 chars in production
- ✅ CORS: env-driven (CORS_ORIGINS / ALLOWED_ORIGINS)
- ✅ Global exception handler: no stack trace leaks to client
- ✅ Structured logging (Gunicorn + Uvicorn workers)
- ✅ PostgreSQL connection pool tuning (pool_pre_ping, pool_recycle)
- ✅ Alembic migrations (3 revisions: initial + password_reset + portfolio_alerts)
- ✅ CI/CD: GitHub Actions — lint, test, build, push on main; test-only on PR
- ✅ Docker: multi-stage builds, non-root user (UID 10001), HEALTHCHECK
- ✅ K8s: security contexts (runAsNonRoot, drop ALL caps), pod anti-affinity

### Password reset flow (complete)
- ✅ PasswordResetToken model, email service, 3 endpoints, anti-enumeration
- ✅ Frontend: forgot-password, reset-password, change-password pages
- ✅ 13/13 password reset tests pass

### Live stock data (complete)
- ✅ stock_data.py: Yahoo Finance chart API, 5-min cache, fail-soft
- ✅ GET /api/stocks/{ticker}/price, GET /api/prices, POST /api/prices/refresh
- ✅ LivePriceTicker component (auto-refresh 60s, live/cached/stale indicators)
- ✅ 17/17 live data tests pass

### Monitoring (complete)
- ✅ metrics.py: Prometheus middleware + /metrics endpoint
- ✅ k8s/monitoring.yaml: ServiceMonitor + standalone Prometheus

### TLS/HTTPS (complete)
- ✅ cert-manager ClusterIssuer, production ingress with TLS + redirect

### Portfolio tracking (complete)
- ✅ Holding model (user_id, ticker, quantity, buy_price, buy_date, unique constraint)
- ✅ GET /api/portfolio — live value enrichment with batch price fetch
- ✅ POST /api/portfolio — upsert with weighted-average buy price
- ✅ PUT /api/portfolio/{ticker} — update holding
- ✅ DELETE /api/portfolio/{ticker} — remove holding
- ✅ PortfolioPage frontend: summary cards (value, cost, P/L, return %), holdings table
- ✅ Add holding form, remove button, empty state, auth guard
- ✅ Navigation: /my-portfolio route with nav link
- ✅ Migration 0003_portfolio_alerts
- ✅ 9/9 portfolio tests pass

### Price alerts (complete)
- ✅ PriceAlert model (user_id, ticker, condition above/below, target_price, triggered)
- ✅ GET /api/alerts, POST /api/alerts, DELETE /api/alerts/{id}
- ✅ POST /api/alerts/check — checks active alerts against live prices
- ✅ PriceAlertsPage frontend: create/delete/check UI, triggered banner
- ✅ Navigation: /alerts route with nav link
- ✅ 9/9 alert tests pass

### Live prices wired into pages (complete)
- ✅ HalalStocksGrid: compact LivePriceTicker on each stock card
- ✅ WatchlistPage: compact LivePriceTicker on each watchlist item

### Tadawul direct scraping (complete)
- ✅ tadawul_scraper.py: Playwright + xvfb bypasses Akamai edge security
- ✅ Three JSON servlet APIs discovered and integrated:
  - TickerServlet → 398 instruments with live price/volume/trades
  - ThemeSearchUtilityServlet → 1871 company directory (symbol, names, ISIN, market_type)
  - ThemeTASIUtilityServlet → TASI/MT30/NOMUC/Sukuk indices, advancers/decliners, market status
- ✅ 5-min TTL in-memory cache, fail-soft (stale fallback), auto xvfb launch
- ✅ test_tadawul_scraper.py: 19 integration tests
- ✅ Requirements updated (playwright>=1.48.0)

### Tadawul API endpoints (complete)
- ✅ GET /api/tadawul/prices — all instruments (optional ?ticker= or ?halal_only=true)
- ✅ GET /api/tadawul/prices/{ticker} — single instrument live price
- ✅ GET /api/tadawul/summary — TASI/MT30/NomuC/Sukuk indices, market status, advancers/decliners
- ✅ GET /api/tadawul/companies — full directory (optional ?market_type= or ?q= search)
- ✅ POST /api/tadawul/cache/refresh — clear scraper cache
- ✅ Rate-limited: 30/min prices, 60/min single, 30/min summary, 20/min companies
- ✅ All fail-soft (503 on scrape failure, stale fallback via scraper cache)
- ✅ 9/9 endpoint tests pass (mocked scraper)

### Research frontend (complete)
- ✅ /research route (web/src/app/[locale]/research/page.tsx) — thin wrapper
- ✅ ResearchPage component (web/src/components/ResearchPage.tsx) — full feature:
  - Auth gate: prompts login/signup if unauthenticated
  - Subscription gate: 402 handling → Pro plan upsell with #pricing link
  - Report generator: ticker input → POST /api/research → polls status every 3s
  - Polling states: pending/running spinner, completed markdown, failed error
  - Report history: GET /api/research/history with cards (ticker, company, rating, date)
  - Sample reports: GET /api/research/samples — public, always visible
  - Full report view: styled markdown (react-markdown + remark-gfm), custom components
  - Rating badges, summary highlight box, status indicators
- ✅ lib/api.ts: researchApi (start, get, history, samples) + billingApi (subscription, checkout, portal)
- ✅ i18n: research section added to both ar.ts and en.ts (30 keys each)
- ✅ Navbar: /research link added (الأبحاث / Research)
- ✅ Footer: research link updated from #discover → /research route
- ✅ react-markdown + remark-gfm installed
- ✅ TypeScript: zero errors
- ✅ Next.js build: passes, /ar/research + /en/research SSG (48.3 kB)

## Next Priorities
1. **Frontend: Tadawul data integration** — wire market page to /api/tadawul/* endpoints (live Tadawul data instead of Yahoo)
2. **/pricing + Stripe checkout frontend** — backend Stripe is fully wired; frontend page missing (research subscription gate links to #pricing which doesn't exist)
3. **US market expansion** — SEC EDGAR data feed for US stocks
4. **Alert notifications** — email/push when alerts trigger (background worker)
5. **Historical charts** — price history graphs on stock detail pages
6. **Portfolio diversification analysis** — sector allocation breakdown
7. **Commit accumulated work** — large uncommitted diff (research frontend + Tadawul API), should be committed in logical chunks
8. **Fix test isolation** — script-style tests fight over database.engine singleton under pytest collection

## Boundaries
- `k8s/postgres-secret.yaml` — gitignored, real secrets live here only
- `backend/stocks.json` — core data, don't overwrite without backup
- `web/src/i18n/{en,ar}.ts` — large files, edit carefully
- `backend/tadawul_scraper.py` — requires `xvfb-run` wrapper in production; Playwright browsers must be pre-installed

## Technical Notes
- saudiexchange.sa Akamai bypass: headed Playwright (headless=False) + xvfb. Headless + stealth JS alone still gets 403.
- Playwright venv: `backend/.venv` (Python 3.12, created via `uv venv --python 3.12 .venv`)
- Browser: Chromium 1228 at `~/.cache/ms-playwright/chromium-1228`
- Each scrape session: ~6-7s (browser launch + nav + fetch). Cache eliminates repeat calls within TTL.
- Node/npm via nvm: `export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"` (node v24.15.0)
- npm cache fix: use `--cache /tmp/npm-cache` if ~/.npm has root-owned files
