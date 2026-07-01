# Mizan (ميزان) — AI Berkshire Saudi Edition

> *Mizan: Arabic for "balance" — the core concept of value investing and the principle of Sharia justice.*

**AI-powered, Sharia-compliant value investing research platform for the Saudi market.**

Built on the proven AI Berkshire framework (69%+ annual returns, two consecutive years),
adapted for Tadawul (the Saudi stock exchange) with AAOIFI-compliant Sharia screening
at every layer.

One person + Mizan = a Sharia-compliant investment research team.

---

## What Problem Does Mizan Solve?

Saudi retail and institutional investors face three pain points that no existing platform addresses:

1. **"Is this stock halal?"** — There is no free, instant, AI-powered Sharia compliance
   checker for Tadawul stocks. Investors rely on static lists published annually by
   scholars that become outdated.

2. **"What does the data actually say?"** — Generic AI tools produce balanced fence-sitting
   analysis ("on one hand... on the other hand..."). They can't make decisions.

3. **"How does this fit Vision 2030?"** — Saudi-specific investment themes (PIF strategy,
   megaprojects, sector diversification) require local market intelligence that no
   Western or Chinese AI tool provides.

Mizan solves all three by combining the AI Berkshire research methodology with
AAOIFI-compliant Sharia screening and Saudi market context.

---

## Three-Tier SaaS Model

### Free Tier — "Sharia Checker"
- Instant Sharia compliance check for any Tadawul-listed stock
- Powered by `tools/sharia_screener.py` (deterministic, AAOIFI Standard 21)
- Bilingual output (Arabic / English)
- **Purpose**: Top-of-funnel. Every Saudi investor needs this. Creates account creation flywheel.

### Pro Tier — SAR 99/month (≈ $26/mo)
- Full investment research reports on Tadawul stocks
- Four-master dialectic analysis (Buffett, Munger, Duan Yongping, Li Lu) with Sharia overlay
- Vision 2030 alignment scoring
- Bilingual deep-dive reports (Arabic + English)
- Portfolio Sharia compliance monitoring
- Email/WhatsApp alerts for thesis changes

### Enterprise Tier — Custom Pricing
- Full investment team workflows (multi-agent parallel research)
- Portfolio-level Sharia compliance audit
- API access for fund managers, family offices, Sharia advisory firms
- Custom sector research (PIF co-investment tracking, megaproject supply chain analysis)
- White-label reports for distribution
- CMA compliance review support

---

## Why Mizan Wins

| Feature | Generic AI (ChatGPT, etc.) | Western Stock Screeners | **Mizan** |
|---------|---------------------------|------------------------|-----------|
| Sharia compliance screening | ❌ Unreliable | ❌ Not available | ✅ **Deterministic, AAOIFI-based** |
| Tadawul market data | ❌ Limited | ⚠️ Partial | ✅ **Native integration** |
| Vision 2030 context | ❌ Generic | ❌ None | ✅ **Built-in** |
| Arabic language support | ⚠️ Basic | ❌ None | ✅ **Arabic-first** |
| Investment verdict (Pass/Fail) | ❌ Fence-sitting | ⚠️ Ratios only | ✅ **Forced conclusion** |
| Multi-agent research | ❌ Single context | ❌ Not applicable | ✅ **4 parallel agents** |
| Track record | ❌ None | N/A | ✅ **69%+ verified returns** |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Mizan SaaS Platform                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Web / Mobile │  │  WhatsApp   │  │  API (Enterprise)   │ │
│  │  Dashboard    │  │  Bot        │  │                     │ │
│  └──────┬───────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                 │                     │            │
│  ┌──────┴─────────────────┴─────────────────────┴──────────┐ │
│  │                   API Gateway Layer                     │ │
│  │         (Auth, Billing, Rate Limiting, i18n)             │ │
│  └──────┬─────────────────┬─────────────────────┬──────────┘ │
│         │                 │                     │            │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌───────────┴──────────┐ │
│  │   Sharia    │  │  Investment │  │   Saudi Market        │ │
│  │   Engine    │  │  Research   │  │   Intelligence        │ │
│  │             │  │  Engine     │  │                       │ │
│  │ AAOIFI 21   │  │ (AI Berk.)  │  │ • Tadawul data        │ │
│  │ Screening   │  │ 18 Skills   │  │ • Vision 2030 scoring │ │
│  │             │  │ 4 Agents    │  │ • PIF tracking        │ │
│  └─────────────┘  └─────────────┘  └───────────────────────┘ │
│         │                 │                     │            │
│  ┌──────┴─────────────────┴─────────────────────┴──────────┐ │
│  │                      Data Layer                          │ │
│  │   Tadawul API • Financial data • News feeds • User DB    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Three Core Engines

1. **Sharia Engine** (`tools/sharia_screener.py`)
   - Deterministic AAOIFI Standard 21 compliance screening
   - Qualitative (sector) + Quantitative (ratio) dual screen
   - Purification calculation
   - Batch screening for portfolio-wide audits

2. **Investment Research Engine** (18 existing AI Berkshire skills)
   - Proven multi-agent methodology with real track record
   - Four-master dialectic analysis
   - Forced verdicts (Pass / Fail / Gray Zone)
   - Financial precision (Decimal arithmetic, cross-validation)

3. **Saudi Market Intelligence** (new layer)
   - Tadawul data adapters (extends existing scrapers)
   - Vision 2030 alignment scoring (does this company benefit from giga-projects?)
   - PIF co-investment tracking (where is the sovereign wealth fund deploying capital?)
   - Arabic report generation

---

## Target Customer Segments

### 1. Retail Investors (Primary — Free + Pro tier)
Saudi Arabia has a rapidly growing retail investor base. Trading accounts surged
from 1.5M to 4.5M+ between 2019-2024. Most are under 35, tech-savvy, and want
Sharia-compliant options.

### 2. Family Offices (Enterprise tier)
~5,000+ ultra-high-net-worth families in Saudi Arabia. They manage significant
portfolios and need Sharia compliance at portfolio scale, not just per-stock.

### 3. Sharia Advisory Firms (Enterprise — API tier)
Licensed Sharia advisory firms (like Alinma Investment, NCB Capital) screen
hundreds of stocks quarterly. Mizan's API can automate the initial screening
pass, letting scholars focus on judgment calls.

### 4. Islamic Finance Students & Researchers (Free tier)
Universities offering Islamic finance degrees (KSA has 50+ programs). Free tier
becomes an educational tool and builds brand loyalty for future professionals.

---

## Go-to-Market Strategy

### Phase 1: Launch (Months 1-3)
- Free Sharia checker goes live as a web app
- Target: 10,000 sign-ups in first quarter
- Channels: Twitter/X (dominant in Saudi), Arabic investing forums, WhatsApp groups
- Content: Weekly "Sharia-compliant stock of the week" social media posts

### Phase 2: Pro Tier Launch (Months 4-6)
- Full research reports on top 50 Tadawul stocks
- Convert 5-10% of free users to Pro (target: 500 paying users)
- Partnerships with Saudi fintech influencers and investing podcasts

### Phase 3: Enterprise (Months 7-12)
- API launch for institutional clients
- Target 3-5 enterprise contracts (family offices, Sharia advisory firms)
- Compliance certifications and CMA engagement

### Phase 4: Regional Expansion (Year 2)
- Expand to UAE (ADX, DFM), Qatar (QE), Kuwait (Boursa)
- Arabic-language mobile app
- Integration with Saudi brokerage platforms

---

## Saudi Market Context: Why Now

- **Tadawul market cap**: ~$2.5 trillion (largest in MENA, 8th globally)
- **Retail investor surge**: 4.5M+ active trading accounts (2024), up from 1.5M in 2019
- **Vision 2030**: Trillion-dollar transformation driving new investment themes
- **PIF (Public Investment Fund)**: $925B sovereign wealth fund actively reshaping markets
- **Regulatory push**: CMA modernizing regulations, encouraging digital investment tools
- **Sharia finance**: Saudi Arabia is the global center of Islamic finance (~$3.8T global market)
- **No dominant AI investment research platform** exists in MENA — wide open market

---

## Technical Foundation

Built on the **AI Berkshire framework** — a battle-tested investment research system
with 18 skills, 9 Python tools, multi-agent parallelism, and a proven real-money track
record (69%+ returns, 2 consecutive years).

**What we keep from AI Berkshire:**
- 18 investment research skills (adapted for Arabic/Saudi context)
- `financial_rigor.py` — exact decimal calculation engine
- Multi-agent parallel research methodology
- Forced-verdict analysis framework
- Anti-bias mechanisms (information richness, inversion, contrarian checks)

**What we add for Saudi:**
- `sharia_screener.py` — AAOIFI Standard 21 compliance engine
- `sharia-screen.md` — Sharia screening skill
- Tadawul data adapters (extends existing `stock_screener.py`, `xueqiu_scraper.py`)
- Arabic report generation (extends existing `wechat-article.md` concept)
- Vision 2030 alignment scoring
- Bilingual (Arabic / English) output throughout

---

## Disclaimer

ميزان is a research and educational tool, not investment advice. Sharia compliance
screening is based on AAOIFI Standard No. 21 and does not constitute a fatwa.
For definitive religious rulings, consult a qualified Sharia scholar.

Past performance of the AI Berkshire framework does not guarantee future results.

---

*Mizan — where value meets values.*
*ميزان — حيث يلتقي القيمة بالقيم*
