# Mizan SaaS Architecture & Build Blueprint
# ميزان — مخطط البناء والتطوير

## 1. Product Vision

**Mizan (ميزان)** transforms the AI Berkshire value investing framework into a
Sharia-compliant, Arabic-first SaaS platform for the Saudi Arabian market.

**Mission**: Give every Saudi investor an institutional-grade, Sharia-compliant
investment research team in their pocket.

**Core Insight**: AI Berkshire already solves "how to analyze stocks with discipline."
The Saudi pivot adds two missing dimensions: (1) "Is this stock halal?" and
(2) "How does this fit the Saudi economic context?" — both at the deterministic
code layer, not left to AI judgment.

---

## 2. Market Sizing

| Metric | Value | Source |
|--------|-------|--------|
| Tadawul market cap | ~$2.5T | Tadawul official |
| Saudi retail trading accounts | 4.5M+ (2024) | CMA reports |
| Saudi retail investor growth | 200% since 2019 | CMA |
| Islamic finance global market | ~$3.8T | ICD-LSEG Islamic Finance Development Report |
| Saudi Islamic banking assets | ~$300B | SAMA |
| Vision 2030 investment pipeline | ~$1T+ | PIF / Vision 2030 docs |
| PIF AUM | ~$925B | PIF 2024 annual report |
| No. of Sharia-compliant stocks on Tadawul | ~70% of listed stocks pass | MSCI Islamic Index screening |

**TAM**: 4.5M retail investors × SAR 99/month × 12 = **SAR 5.3 billion/year**
(maximum theoretical, if every active investor subscribed — unrealistic but shows scale)

**SAM** (realistic addressable): ~500K active, engaged investors × 5% conversion × SAR 99 × 12
= **SAR 29.7 million/year** in Pro revenue (Year 2 target)

**Enterprise SAM**: ~5,000 family offices + Sharia advisory firms × SAR 50K-200K/year
= **SAR 250M-1B/year** (long-term potential)

---

## 3. Product Architecture

### 3.1 Three Core Engines

#### Engine 1: Sharia Compliance Engine
- **Status**: ✅ BUILT (`tools/sharia_screener.py`)
- **Standard**: AAOIFI Standard No. 21
- **Features**: Qualitative (sector) + Quantitative (ratio) dual screen, batch mode, purification calculation
- **CLI exit codes**: 0 = compliant, 1 = non-compliant (CI/CD friendly)

#### Engine 2: Investment Research Engine
- **Status**: ✅ EXISTS (18 skills from AI Berkshire)
- **Adaptation needed**: Arabic localization, Tadawul data sources, Vision 2030 scoring overlay
- **Key skills to adapt first**: `/investment-research`, `/investment-checklist`, `/quality-screen`

#### Engine 3: Saudi Market Intelligence
- **Status**: 🔨 TO BUILD
- **Components**:
  - Tadawul data adapter (extends `tools/xueqiu_scraper.py` pattern)
  - Vision 2030 alignment scorer
  - PIF co-investment tracker
  - Arabic financial terminology NLP layer
  - News aggregator (Saudi-focused sources)

### 3.2 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js + Tailwind | SSR for SEO, Arabic RTL support, fast |
| Backend API | FastAPI (Python) | Same language as existing tools, async |
| AI Engine | Claude API + Codex | Existing framework compatibility |
| Database | PostgreSQL | ACID for financial data, JSON for reports |
| Cache | Redis | Screen results, session data |
| Queue | Celery / Redis Queue | Background research jobs |
| Deployment | AWS (me-central-1, Bahrain) | Closest region to Saudi Arabia |
| Auth | OAuth 2.0 (Apple, Google, Twitter) | Saudi users expect social login |
| Payments | Stripe + mada (Saudi debit) | mada is mandatory for local cards |
| Monitoring | Sentry + CloudWatch | Production observability |

### 3.3 Data Sources

| Source | Data | Cost | Priority |
|--------|------|------|----------|
| Tadawul official API | OHLCV, fundamentals | TBD | P0 |
| Saudi Stock Watch / Argaam | Financial data, news | Low (scraping) | P0 |
| Mubasher / Investing.com Saudi | Fundamentals | Low | P1 |
| MSCI Islamic Index | Sharia compliance reference | Free (public constituents) | P0 |
| CMA disclosures | Regulatory filings | Free | P1 |
| Company IR pages | Financial statements (Arabic) | Free (scraping) | P1 |
| Saudi Press Agency (SPA) | News | Free | P2 |
| Arabic financial news (Alyaum, Eqtesadiah) | News, analysis | Low | P2 |

---

## 4. Business Model

### 4.1 Pricing

| Tier | Price | Target Users | Key Features |
|------|-------|-------------|--------------|
| **Free** | SAR 0 | All Saudi investors | Sharia checker, basic stock info, news feed |
| **Pro** | SAR 99/month (~$26) | Serious retail investors | Full research reports, portfolio monitoring, alerts, bilingual reports |
| **Enterprise** | SAR 50K-200K/year | Family offices, advisory firms | API access, custom workflows, white-label, audit reports |

### 4.2 Revenue Projections (Conservative)

| Period | Free Users | Pro Users | Enterprise | Monthly Revenue |
|--------|-----------|----------|------------|----------------|
| Month 3 | 10,000 | 0 | 0 | SAR 0 |
| Month 6 | 25,000 | 300 (1.2%) | 0 | SAR 29,700/mo |
| Month 12 | 75,000 | 1,500 (2%) | 2 contracts | SAR 149K/mo + SAR 12M/yr |
| Month 24 | 200,000 | 5,000 (2.5%) | 8 contracts | SAR 495K/mo + SAR 50M/yr |

### 4.3 Unit Economics

| Metric | Value | Notes |
|--------|-------|-------|
| CAC (Pro tier) | ~SAR 50 | Social media + referrals |
| LTV (Pro tier, 2yr avg) | SAR 2,376 | SAR 99 × 24 months |
| LTV/CAC | 47.5x | Very healthy |
| Gross margin | ~80% | AI API costs are main variable |
| AI API cost per report | ~$2-5 | Claude API usage per deep report |
| Break-even | ~1,200 Pro users | Covers infra + 2 FTEs |

---

## 5. Development Roadmap

### Phase 0: Foundation (Weeks 1-4) ✅ IN PROGRESS
- [x] Clone AI Berkshire codebase
- [x] Build `sharia_screener.py` — AAOIFI screening engine
- [x] Write `sharia-screen.md` — Sharia screening skill
- [x] Create SaaS architecture document
- [ ] Build Tadawul data adapter (extends existing scraper pattern)
- [ ] Create `saudi-market-context.md` skill (Vision 2030, PIF, megaprojects)

### Phase 1: MVP — Free Tier (Weeks 5-12)
- [ ] Web app: single-page Sharia checker (input ticker → get verdict)
- [ ] Tadawul stock database (top 200 companies by market cap)
- [ ] Bilingual UI (Arabic RTL + English)
- [ ] User accounts (email + social login)
- [ ] Deploy to AWS me-central-1
- [ ] Social media launch campaign

### Phase 2: Pro Tier (Weeks 13-24)
- [ ] Full investment research pipeline for Tadawul stocks
- [ ] Adapt 3-5 core skills for Arabic output
- [ ] Portfolio Sharia compliance monitoring dashboard
- [ ] Alert system (WhatsApp / email)
- [ ] Billing integration (Stripe + mada)
- [ ] Vision 2030 alignment scoring
- [ ] Mobile-responsive web app

### Phase 3: Enterprise (Weeks 25-40)
- [ ] REST API with API key auth
- [ ] Batch screening endpoint
- [ ] White-label report generation
- [ ] Portfolio audit reports
- [ ] Rate limiting and usage analytics
- [ ] Enterprise sales outreach

### Phase 4: Mobile App (Year 2)
- [ ] React Native mobile app
- [ ] Push notifications for thesis changes
- [ ] Social features (watchlist sharing, community)
- [ ] Brokerage integration (Al Rajhi Capital, NCB Capital)

---

## 6. Saudi-Specific Design Decisions

### 6.1 Arabic-First
- All reports generated in both Arabic and English
- Arabic RTL layout throughout the web app
- Financial terminology uses standard Arabic finance terms (not translated English)
- Voice/WhatsApp interface in Arabic dialect (Khaliji)

### 6.2 Sharia Compliance as a Precondition
- Every investment research workflow runs the Sharia screen FIRST
- Non-compliant stocks are excluded from analysis by default
- Users can override (for research purposes) but must explicitly acknowledge

### 6.3 Vision 2030 Context
Each company analysis includes a "Vision 2030 Alignment Score":
- **Direct beneficiary**: Company is a PIF portfolio company or Vision 2030 contractor
- **Indirect beneficiary**: Company operates in a sector targeted for growth
- **Neutral**: No significant Vision 2030 impact
- **At risk**: Company's sector may be disrupted by Vision 2030 reforms

### 6.4 Regulatory Compliance
- Mizan does NOT provide investment advice (research/educational tool)
- CMA (Capital Market Authority) licensing considerations for paid tiers
- SAMA (Saudi Central Bank) compliance for any banking-related features
- Data residency: user data stored in-region (AWS Bahrain or future Saudi region)

---

## 7. Competitive Moat

1. **Sharia screener is deterministic code** — competitors can't replicate accuracy by asking AI
2. **AI Berkshire's proven methodology** — 69%+ returns is a track record no competitor has
3. **Bilingual from the ground up** — not bolted-on translation, but native Arabic
4. **Saudi market-specific intelligence** — Vision 2030, PIF, Tadawul data integration
5. **Open source core** — the underlying AI Berkshire is public, building trust and community

---

## 8. Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Tadawul API access restricted | High | Use multiple data sources (Arqaam, Mubasher, scraping) |
| CMA regulatory pushback | Medium | Position as research tool, not advisory. Engage CMA early. |
| AI API costs scale with users | Medium | Cache results, batch processing, tiered query limits |
| Arabic NLP quality | Medium | Use Claude/GPT-4 for Arabic (both strong in Arabic) |
| Competitor enters market | Low-Medium | First-mover advantage, build community, ship fast |
| Sharia screen accuracy disputes | Medium | Use AAOIFI standard (global consensus), disclose methodology, recommend scholar consultation |

---

## 9. Team Requirements (Phase 1)

| Role | Priority | Could be... |
|------|----------|-------------|
| Product / AI Lead | P0 | Existing AI Berkshire author + Claude Code |
| Full-stack Developer | P0 | 1 hire (Python + Next.js) |
| Arabic Content / Sharia Review | P1 | Part-time consultant (Sharia finance background) |
| Growth / Social Media | P1 | Part-time (Saudi Twitter/X native) |
| Enterprise Sales | P2 | Founder-led initially |

**Burn rate (Phase 1, 3 months)**: ~SAR 60K-90K/month (2 FTEs + infra + AI APIs)

---

## 10. Open Questions

- [ ] Tadawul official API: what's the access model and cost?
- [ ] CMA: does a "research tool" need licensing? What are the boundaries?
- [ ] mada payment integration: what's the merchant onboarding process for a SaaS?
- [ ] Should Mizan be a separate legal entity (Saudi LLC) or operate under existing structure?
- [ ] Arabic dialect: Modern Standard Arabic (formal) vs Saudi dialect (conversational) for reports?
- [ ] Should we partner with an existing Saudi fintech or brokerage for distribution?

---

*Document status: Living document. Update as decisions are made.*
*Last updated: 2025-01-25*
