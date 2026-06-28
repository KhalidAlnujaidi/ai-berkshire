# Mizan Roadmap

## ✅ Completed

### Sharia Screening Engine
- AAOIFI Standard No. 21 compliance engine (`tools/sharia_screener.py`)
- Dual screen: qualitative (sector) + quantitative (6 financial ratios)
- Exact Decimal arithmetic (28-digit precision)
- 49 Saudi stocks in database, 14 halal

### Web Platform (Next.js 14)
- **Sharia Checker** — instant stock screening with animated ratio bars
- **Halal Stocks Grid** — browse pre-filtered halal universe by sector
- **Stock Detail Pages** — full screening breakdown per stock (`/stock/[ticker]`)
- **Stock Comparison** — side-by-side comparison of up to 3 stocks (`/compare`)
- **Portfolio Screener** — weighted Sharia assessment of entire portfolio (`/portfolio`)
- **Education Center** — Sharia investment academy explaining AAOIFI standards (`/learn`)
- **Market Dashboard** — sector heatmap, compliance donut, top halal stocks leaderboard, market cap analytics (`/market`)
- **Watchlist** — star/bookmark stocks, re-screen on demand, change detection (`/watchlist`)
- **Zakat Calculator** — Islamic zakat on investments with dynamic nisab (`/zakat`)
- **Purification Calculator** — income purification with auto/manual modes (`/purification`)
- **Auth Pages** — login & signup with social auth UI (`/login`, `/signup`)
- **Legal Pages** — Privacy Policy, Terms, Disclaimer, About, Contact
- **Custom 404** — branded bilingual not-found page
- Full bilingual support (Arabic RTL / English LTR)
- Responsive design (mobile, tablet, desktop)
- SEO: sitemap.xml (30 URLs), robots.ts, JSON-LD, PWA manifest
- localStorage-based watchlist persistence

### Backend API (FastAPI — v1.4.0)
- `GET /api/health` — health check
- `GET /api/stocks` — list all stocks (with sector filter)
- `GET /api/stocks/{ticker}` — single stock with full Sharia verdict
- `GET /api/halal-stocks` — pre-filtered halal-only universe
- `GET /api/search?q=` — search by ticker, Arabic name, or English name
- `POST /api/sharia-screen` — custom company screening
- `POST /api/portfolio-screen` — portfolio-level compliance analysis
- `GET /api/stats` — market-wide compliance statistics
- `GET /api/market` — comprehensive market dashboard data (sectors, top stocks, ratios)
- 11 backend tests, all passing

## P0: Near-term (Pre-Launch)

### Polish & Deploy
- App icons (192px / 512px PNGs for PWA)
- Open Graph image for social sharing
- Deploy backend to Render/Railway → `api.mizan-invest.com`
- Deploy frontend to Vercel → `mizan-invest.com`
- Performance audit (Lighthouse > 90)
- Accessibility audit (WCAG 2.1 AA)

### US Market Expansion
- Add US stocks (AAPL, MSFT, GOOGL, etc.) via SEC EDGAR / yfinance
- Generate templates with `python3 tools/update_stocks_data.py template --ticker AAPL --market us`
- Market-agnostic engine already supports this — only data layer needs expansion

### Real-time Data Integration
- Connect to Tadawul API for live stock prices
- Auto-update financial ratios quarterly from earnings reports
- Alert users when a halal stock's ratios drift toward non-compliance

## P1: Mid-term (3-6 months)

### User Accounts & Saved Portfolios
- Supabase / Clerk authentication
- Persist portfolios across sessions
- Email/WhatsApp alerts when compliance status changes

### Investment Research Reports
- Deep-dive AI analysis (Buffett/Munger methodology)
- Vision 2030 alignment scoring
- HTML report export with charts and visualizations
- Multi-depth modes: lite / standard / deep

### Watchlists & Alerts
- Server-side watchlists (currently localStorage)
- Push notifications for ratio threshold breaches
- Quarterly re-screening reminders

## P2: Long-term (6 months+)

### Portfolio Analytics
- Sector concentration analysis
- Correlation risk detection
- Geographic diversification scoring
- Historical compliance tracking

### API Platform (Enterprise)
- REST API for third-party integration
- Rate limiting and API keys
- White-label screening widget
- Webhook notifications

### Additional Markets
- Hong Kong (HKEX)
- Indonesia (IDX)
- Malaysia (Bursa Malaysia)
- UK (LSE)

## Testing Coverage
- Expand backend test suite (unit tests for each screener function)
- Frontend component tests (React Testing Library)
- E2E tests (Playwright) for critical user flows
- Regression tests for i18n completeness
