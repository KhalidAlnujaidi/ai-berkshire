# Mizan ↔ TradingAgents Bridge Architecture

> The SaaS emerges from wiring these two resources together. This document
> defines the bridge layer — the API, data flow, and rendering pipeline that
> turns TradingAgents' multi-agent analysis into Arabic-first structured data
> the Mizan frontend can display.

---

## 1. Why a Bridge, Not a Merge

Both systems stay independent. The bridge is a **thin orchestration layer** inside
Mizan's backend that:

1. Accepts a ticker from an authenticated user
2. Invokes `TradingAgentsGraph.propagate()` as a background job
3. Stores the structured result
4. Serves it to the frontend as JSON the UI renders in Arabic

**Key enabler**: Both are Python. TradingAgents is a pip-installable package.
No microservice, no message queue, no second deployment — initially. The
`TradingAgentsGraph` class is imported directly into Mizan's FastAPI process.

---

## 2. Verified API Contracts

> These were confirmed by reading the actual source code of both projects.
> Every field name and type below is real, not assumed.

### 2.1 TradingAgentsGraph — what the bridge calls

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = TradingAgentsGraph(config={...})
# propagate() returns a TUPLE of (final_state_dict, rating_string)
final_state, rating = ta.propagate(company_name="2222.SR", trade_date="2025-01-15")
```

**Return contract**: `propagate()` → `(final_state: dict, signal: str)`
- `signal` is a string: one of `"Buy" | "Overweight" | "Hold" | "Underweight" | "Sell"`
- `final_state` is a flat dict with these keys:

| Key | Type | Source |
|-----|------|--------|
| `company_of_interest` | str | The ticker passed in |
| `trade_date` | str | The date passed in |
| `market_report` | str (markdown) | Market Analyst agent |
| `fundamentals_report` | str (markdown) | Fundamentals Analyst agent |
| `sentiment_report` | str (markdown) | Sentiment Analyst agent (structured → rendered) |
| `news_report` | str (markdown) | News Analyst agent |
| `investment_debate_state` | dict | Bull/Bear debate + judge decision |
| `investment_plan` | str (markdown) | Research Manager (rendered from `ResearchPlan`) |
| `trader_investment_plan` | str (markdown) | Trader (rendered from `TraderProposal`) |
| `risk_debate_state` | dict | Aggressive/Conservative/Neutral debate + judge |
| `final_trade_decision` | str (markdown) | Portfolio Manager (rendered from `PortfolioDecision`) |

**Debate state dicts**:
```python
investment_debate_state = {
    "bull_history": str,       # full bull argument
    "bear_history": str,       # full bear argument
    "judge_decision": str,     # research manager's ruling
}
risk_debate_state = {
    "aggressive_history": str,
    "conservative_history": str,
    "neutral_history": str,
    "judge_decision": str,
}
```

### 2.2 Structured output schemas (exist inside TradingAgents)

TradingAgents has Pydantic schemas for its decision agents, but **renders them
to markdown** before storing in `final_state`. The bridge receives markdown
strings, not parsed objects.

The known markdown patterns (from `render_*` functions):

```python
# PortfolioDecision → final_trade_decision
**Rating**: Buy
**Executive Summary**: ...
**Investment Thesis**: ...
**Price Target**: 32.5
**Time Horizon**: 3-6 months

# TraderProposal → trader_investment_plan
**Action**: Buy
**Reasoning**: ...
**Entry Price**: 30.0
**Stop Loss**: 27.5
**Position Sizing**: 5% of portfolio
FINAL TRANSACTION PROPOSAL: **BUY**

# ResearchPlan → investment_plan
**Recommendation**: Buy
**Rationale**: ...
**Strategic Actions**: ...
```

**Bridge strategy**: Parse these known markdown patterns into structured
fields using the `**Field Name**: value` format. This is deterministic —
no LLM needed for extraction. A `parse_markdown_fields()` utility handles it.

### 2.3 TradingAgents config keys (verified from `DEFAULT_CONFIG`)

```python
DEFAULT_CONFIG = {
    "llm_provider": "openai",        # "openai" | "google" | "anthropic"
    "deep_think_llm": "gpt-5.5",     # the heavy reasoning model
    "quick_think_llm": "gpt-5.4-mini",  # the fast model
    "backend_url": None,             # custom LLM endpoint (e.g. OpenRouter)
    "output_language": "English",    # final report language
    "max_debate_rounds": 1,          # bull/bear rounds
    "max_risk_discuss_rounds": 1,    # risk discussion rounds
    "max_recur_limit": 100,
    "news_article_limit": 20,
    "checkpoint_enabled": False,     # resume after crash
    "benchmark_ticker": None,
    "data_vendors": {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
        "macro_data": "fred",
        "prediction_markets": "polymarket",
    },
}
```

Env overrides via `TRADINGAGENTS_*` prefix: `TRADINGAGENTS_LLM_PROVIDER`,
`TRADINGAGENTS_DEEP_THINK_LLM`, `TRADINGAGENTS_OUTPUT_LANGUAGE`, etc.

### 2.4 Mizan backend — where the bridge plugs in

Mizan's backend is a single `app.py` FastAPI file with:
- SQLAlchemy models in `models.py`
- Pydantic schemas in `schemas.py`
- SQLite database via `database.py`
- JWT auth via `auth.py`
- Existing routes: `/api/auth/*`, `/api/stocks`, `/api/portfolio`, `/api/watchlist`, `/api/sharia-screen`, `/api/alerts`

The bridge adds new routes to the same `app.py` (or a blueprint/router) and
new models to `models.py`. No changes to existing code.

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Mizan Frontend (Next.js)                  │
│                                                              │
│  Portfolio │ Watchlist │ Sharia Screen │ AI Analysis ★       │
│                                            (Pro tier)        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS / JWT
┌──────────────────────▼──────────────────────────────────────┐
│                  Mizan Backend (FastAPI)                      │
│                                                              │
│  Existing endpoints          │  NEW: Bridge endpoints         │
│  /api/auth/*                 │  POST /api/analysis             │
│  /api/stocks                 │  GET  /api/analysis/{id}        │
│  /api/portfolio              │  GET  /api/analysis/history     │
│  /api/watchlist              │  GET  /api/analysis/{ticker}/latest │
│  /api/sharia-screen          │                                │
│  /api/alerts                 │  NEW: AnalysisService           │
│                              │  ├── enqueue analysis job       │
│                              │  ├── poll job status            │
│                              │  └── parse → translate → store  │
│                              │                                │
│  SQLite DB                   │  NEW TABLE: analysis_reports    │
│  users, holdings, alerts…    │                                │
└──────────────────────┬──────────────────────────────────────┘
                       │ Python import (in-process)
┌──────────────────────▼──────────────────────────────────────┐
│              TradingAgents (Python package)                   │
│                                                              │
│  TradingAgentsGraph                                          │
│  .propagate(ticker, date)                                    │
│  → (final_state, rating)                                     │
│                                                              │
│  final_state keys:                                           │
│    market_report, fundamentals_report,                       │
│    sentiment_report, news_report                             │
│    investment_debate_state: {bull, bear, judge}              │
│    investment_plan (ResearchPlan → markdown)                 │
│    trader_investment_plan (TraderProposal → markdown)        │
│    risk_debate_state: {aggressive, conservative,             │
│                        neutral, judge}                       │
│    final_trade_decision (PortfolioDecision → markdown)       │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Data Flow (Happy Path)

```
User clicks "تحليل بالذكاء الاصطناعي" (AI Analysis) on a stock page
  │
  ▼
POST /api/analysis  { ticker: "2222.SR" }
  │  (auth required, Pro tier check)
  ▼
Backend creates AnalysisReport row (status=pending)
  │
  ▼
Background task starts:
  1. Initialize TradingAgentsGraph with config
  2. final_state, rating = ta.propagate(ticker, today)
  3. Wait 2-5 min (agents debate, call LLMs, fetch data)
  4. Parse markdown fields → structured dict (deterministic)
  5. Translate structured fields to Arabic (one LLM call)
  6. Store result_json in AnalysisReport
  7. Update status=completed
  │
  ▼
Frontend polls GET /api/analysis/{id} every 5s
  │  (shows spinner: "يحلل الوكلاء..." / "Agents analyzing...")
  ▼
Status: completed → frontend renders analysis dashboard:
  - Executive summary (Arabic)
  - Recommendation badge (Buy/Hold/Sell with Arabic labels)
  - Bull vs Bear debate (expandable sections)
  - Analyst reports (4 tabs: market, fundamentals, sentiment, news)
  - Risk management assessment
  - Price target and position sizing
```

---

## 5. New API Contracts

### 5.1 Request Analysis

```
POST /api/analysis
Authorization: Bearer <jwt>
Content-Type: application/json

Request:
{
  "ticker": "2222.SR",
  "depth": "standard"          // "standard" | "deep" (deep = more debate rounds)
}

Response 202 (Accepted):
{
  "analysis_id": 42,
  "status": "pending",
  "ticker": "2222.SR",
  "estimated_seconds": 180,
  "poll_url": "/api/analysis/42"
}

Errors:
  401 — not authenticated
  403 — not Pro tier (subscription required)
  409 — analysis already running for this ticker+user (return existing pending job)
  429 — rate limit (max N analyses per day per user)
```

### 5.2 Poll Analysis Status

```
GET /api/analysis/{analysis_id}
Authorization: Bearer <jwt>

Response 200 (while pending):
{
  "analysis_id": 42,
  "status": "running",        // "pending" → "running" → "completed" | "failed"
  "ticker": "2222.SR"
}

Response 200 (completed):
{
  "analysis_id": 42,
  "status": "completed",
  "ticker": "2222.SR",
  "completed_at": "2025-01-15T14:32:00Z",
  "result": { ... }           // see §6 — AnalysisResult schema
}

Response 200 (failed):
{
  "analysis_id": 42,
  "status": "failed",
  "error": "فشل الاتصال بمزود التحليل"   // Arabic user-facing error
}
```

### 5.3 Analysis History

```
GET /api/analysis/history?ticker=2222.SR&limit=10
Authorization: Bearer <jwt>

Response 200:
{
  "analyses": [
    {
      "analysis_id": 42,
      "ticker": "2222.SR",
      "status": "completed",
      "rating": "Buy",
      "completed_at": "2025-01-15T14:32:00Z"
    }
  ]
}
```

### 5.4 Latest Analysis for Ticker

```
GET /api/analysis/{ticker}/latest
Authorization: Bearer <jwt>

Response 200: same as §5.2 completed response
Response 404: no analysis exists for this ticker
```

---

## 6. AnalysisResult Schema (the JSON the frontend consumes)

Stored in `analysis_reports.result_json`. Designed so the frontend renders
every section without parsing markdown.

```json
{
  "meta": {
    "ticker": "2222.SR",
    "name_ar": "أرامكو السعودية",
    "analysis_date": "2025-01-15",
    "generated_at": "2025-01-15T14:32:00Z",
    "framework_version": "0.3.0",
    "models_used": {
      "deep_think": "gpt-5.5",
      "quick_think": "gpt-5.4-mini"
    }
  },

  "recommendation": {
    "rating": "Buy",
    "rating_ar": "شراء",
    "executive_summary_ar": "بناءً على التحليل الشامل...",
    "investment_thesis_ar": "أرامكو السعودية تتمتع ب...",
    "price_target": 32.5,
    "price_target_currency": "SAR",
    "time_horizon": "3-6 months"
  },

  "trader_proposal": {
    "action": "Buy",
    "action_ar": "شراء",
    "reasoning_ar": "الإجراء الموصى به هو الشراء...",
    "entry_price": 30.0,
    "stop_loss": 27.5,
    "position_sizing": "5% of portfolio"
  },

  "analysts": {
    "market": {
      "title_ar": "تحليل السوق",
      "summary_ar": "...",
      "raw_markdown": "..."
    },
    "fundamentals": {
      "title_ar": "التحليل الأساسي",
      "summary_ar": "...",
      "raw_markdown": "..."
    },
    "sentiment": {
      "title_ar": "تحليل المشاعر",
      "summary_ar": "...",
      "raw_markdown": "..."
    },
    "news": {
      "title_ar": "تحليل الأخبار",
      "summary_ar": "...",
      "raw_markdown": "..."
    }
  },

  "research_debate": {
    "bull_case_ar": "...",
    "bear_case_ar": "...",
    "manager_decision_ar": "..."
  },

  "risk_assessment": {
    "aggressive_view_ar": "...",
    "conservative_view_ar": "...",
    "neutral_view_ar": "...",
    "manager_decision_ar": "..."
  },

  "sharia_context": {
    "verdict": "compliant",
    "verdict_ar": "متوافق",
    "note_ar": "هذا السهم اجتاز الفحص الشرعي..."
  }
}
```

---

## 7. New Database Model

```sql
CREATE TABLE analysis_reports (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    ticker        TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    -- 'pending' | 'running' | 'completed' | 'failed'

    config_json   TEXT,          -- what config was used (models, debate rounds)
    result_json   TEXT,          -- AnalysisResult schema (§6), NULL until completed

    error_message TEXT,          -- Arabic user-facing error if failed
    rating        TEXT,          -- denormalized from result for fast queries

    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at  TIMESTAMP
);

CREATE INDEX idx_analysis_user ON analysis_reports(user_id);
CREATE INDEX idx_analysis_ticker ON analysis_reports(ticker);
CREATE INDEX idx_analysis_status ON analysis_reports(status);
```

Pro tier fields on existing users table:

```sql
ALTER TABLE users ADD COLUMN is_pro BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN pro_expires_at TIMESTAMP;
```

---

## 8. Markdown → Structured Extraction

TradingAgents renders its Pydantic decision objects into markdown before
storing them in `final_state`. The bridge parses them back using the known
`**Field**: value` patterns. This is a deterministic utility, not an LLM call.

```python
# backend/analysis_parser.py (new file)

import re
from typing import Any

def parse_markdown_fields(markdown: str) -> dict[str, str]:
    """Parse '**Field Name**: value' patterns from rendered markdown.
    
    TradingAgents' render_* functions produce deterministic markdown with
    this exact format. This function extracts each field deterministically.
    """
    pattern = r'^\*\*(.+?)\*\*:\s*(.+)$'
    fields = {}
    for line in markdown.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            key = match.group(1).strip().lower().replace(' ', '_')
            fields[key] = match.group(2).strip()
    return fields

def extract_portfolio_decision(markdown: str) -> dict[str, Any]:
    """Extract structured fields from PortfolioDecision markdown."""
    fields = parse_markdown_fields(markdown)
    result = {
        "rating": fields.get("rating", "Hold"),
        "executive_summary": fields.get("executive_summary", ""),
        "investment_thesis": fields.get("investment_thesis", ""),
        "price_target": None,
        "time_horizon": fields.get("time_horizon"),
    }
    # Try to parse numeric fields
    if "price_target" in fields:
        try:
            result["price_target"] = float(fields["price_target"])
        except ValueError:
            pass
    return result

def extract_trader_proposal(markdown: str) -> dict[str, Any]:
    """Extract structured fields from TraderProposal markdown."""
    fields = parse_markdown_fields(markdown)
    result = {
        "action": fields.get("action", "Hold"),
        "reasoning": fields.get("reasoning", ""),
        "entry_price": None,
        "stop_loss": None,
        "position_sizing": fields.get("position_sizing"),
    }
    for num_field in ("entry_price", "stop_loss"):
        if num_field in fields:
            try:
                result[num_field] = float(fields[num_field])
            except ValueError:
                pass
    return result
```

---

## 9. Translation Strategy

**Problem**: TradingAgents reasoning quality is best in English. Its
`output_language` config exists but setting it to "Arabic" risks degrading
the multi-agent debate.

**Solution**: Two-layer approach.

| Layer | Language | Rationale |
|-------|----------|-----------|
| Agent reasoning (internal) | English | Maximum reasoning quality. This is the bull/bear debate, risk discussion — the intelligence. |
| Structured outputs shown to user | Arabic | Translated after the fact by a single LLM call per section. |

**Translation pass**: After `propagate()` completes, a single batched LLM
call translates all structured fields to Arabic. We translate only the final
structured fields (executive summary, investment thesis, analyst summaries,
debate conclusions) — not raw agent transcripts. This is ~10 short
translations in one LLM call, ~10 seconds.

The raw English markdown is preserved in `raw_markdown` fields behind a
"النص الأصلي" (Original text) toggle for advanced users who want the
untranslated analysis.

```python
# Pseudocode for the translation pass
async def translate_to_arabic(self, result: dict) -> dict:
    """One LLM call translates all _ar fields."""
    fields_to_translate = {
        "executive_summary": result["recommendation"]["executive_summary_en"],
        "investment_thesis": result["recommendation"]["investment_thesis_en"],
        "market_summary": result["analysts"]["market"]["summary_en"],
        # ... etc for each section
    }
    
    prompt = f"""Translate the following investment analysis fields to Arabic.
    Use professional financial Arabic. Return JSON with the same keys.
    
    {json.dumps(fields_to_translate, ensure_ascii=False)}
    """
    
    translated = await llm.call(prompt, response_format="json")
    # Merge translated fields back into result
    return result
```

**Rating Arabic mapping** (static, no LLM needed):

| English | Arabic |
|---------|--------|
| Buy | شراء |
| Overweight | زيادة الوزن |
| Hold | انتظار |
| Underweight | نقص الوزن |
| Sell | بيع |

---

## 10. AnalysisService Implementation

```python
# backend/analysis_service.py (new file)

import asyncio
import json
import logging
from datetime import datetime, date
from typing import Any

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

from analysis_parser import extract_portfolio_decision, extract_trader_proposal
from database import SessionLocal
from models import AnalysisReport

logger = logging.getLogger(__name__)

# Rating translation table (static — no LLM needed)
RATING_AR = {
    "Buy": "شراء",
    "Overweight": "زيادة الوزن",
    "Hold": "انتظار",
    "Underweight": "نقص الوزن",
    "Sell": "بيع",
}


class AnalysisService:
    """Wraps TradingAgentsGraph for the Mizan backend.
    
    Singleton — TradingAgentsGraph holds LLM clients in memory and takes
    ~5 seconds to initialize. We create it once and reuse.
    """
    
    _instance = None
    _ta: TradingAgentsGraph | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_graph(self) -> TradingAgentsGraph:
        """Lazy-initialize the TradingAgentsGraph singleton."""
        if self._ta is None:
            config = DEFAULT_CONFIG.copy()
            config["output_language"] = "English"    # reasoning in English
            config["max_debate_rounds"] = 1          # standard tier
            config["max_risk_discuss_rounds"] = 1
            logger.info("Initializing TradingAgentsGraph (one-time)...")
            self._ta = TradingAgentsGraph(config=config)
            logger.info("TradingAgentsGraph ready")
        return self._ta

    async def run_analysis(self, ticker: str, analysis_id: int):
        """Called as a FastAPI background task.
        
        This is the core bridge method. It:
        1. Runs TradingAgents.propagate() in a thread (it's sync/blocking)
        2. Parses the markdown final_state into structured fields
        3. Translates structured fields to Arabic
        4. Saves the result to the database
        """
        db = SessionLocal()
        try:
            # Update status to running
            report = db.query(AnalysisReport).get(analysis_id)
            report.status = "running"
            db.commit()

            # propagate() is synchronous and blocking (2-5 min)
            # Run it in a thread pool to not block the event loop
            ta = self._get_graph()
            today = date.today().isoformat()
            
            loop = asyncio.get_event_loop()
            final_state, rating = await loop.run_in_executor(
                None,
                lambda: ta.propagate(company_name=ticker, trade_date=today)
            )

            # Parse markdown → structured fields
            pm = extract_portfolio_decision(final_state["final_trade_decision"])
            trader = extract_trader_proposal(final_state["trader_investment_plan"])

            # Build the AnalysisResult schema
            result = {
                "meta": {
                    "ticker": ticker,
                    "analysis_date": today,
                    "generated_at": datetime.utcnow().isoformat(),
                    "models_used": {
                        "deep_think": ta.config["deep_think_llm"],
                        "quick_think": ta.config["quick_think_llm"],
                    },
                },
                "recommendation": {
                    "rating": pm["rating"],
                    "rating_ar": RATING_AR.get(pm["rating"], pm["rating"]),
                    "executive_summary_en": pm["executive_summary"],
                    "investment_thesis_en": pm["investment_thesis"],
                    "price_target": pm.get("price_target"),
                    "time_horizon": pm.get("time_horizon"),
                },
                "trader_proposal": {
                    "action": trader["action"],
                    "action_ar": RATING_AR.get(trader["action"], trader["action"]),
                    "reasoning_en": trader["reasoning"],
                    "entry_price": trader.get("entry_price"),
                    "stop_loss": trader.get("stop_loss"),
                    "position_sizing": trader.get("position_sizing"),
                },
                "analysts": {
                    "market": {"raw_markdown": final_state["market_report"]},
                    "fundamentals": {"raw_markdown": final_state["fundamentals_report"]},
                    "sentiment": {"raw_markdown": final_state["sentiment_report"]},
                    "news": {"raw_markdown": final_state["news_report"]},
                },
                "research_debate": {
                    "bull_case_en": final_state["investment_debate_state"]["bull_history"],
                    "bear_case_en": final_state["investment_debate_state"]["bear_history"],
                    "manager_decision_en": final_state["investment_debate_state"]["judge_decision"],
                },
                "risk_assessment": {
                    "aggressive_view_en": final_state["risk_debate_state"]["aggressive_history"],
                    "conservative_view_en": final_state["risk_debate_state"]["conservative_history"],
                    "neutral_view_en": final_state["risk_debate_state"]["neutral_history"],
                    "manager_decision_en": final_state["risk_debate_state"]["judge_decision"],
                },
            }

            # Translate to Arabic (Phase 2 — skip in MVP)
            # result = await self._translate_to_arabic(result)

            # Save
            report.status = "completed"
            report.rating = pm["rating"]
            report.result_json = json.dumps(result, ensure_ascii=False)
            report.completed_at = datetime.utcnow()
            db.commit()

            logger.info(f"Analysis {analysis_id} completed: {ticker} → {pm['rating']}")

        except Exception as e:
            logger.exception(f"Analysis {analysis_id} failed: {e}")
            report = db.query(AnalysisReport).get(analysis_id)
            report.status = "failed"
            report.error_message = "فشل التحليل. يرجى المحاولة مرة أخرى."
            db.commit()
        finally:
            db.close()
```

---

## 11. API Endpoint Implementation

```python
# Added to backend/app.py (or a new router module)

from fastapi import BackgroundTasks
from models import AnalysisReport
from analysis_service import AnalysisService

service = AnalysisService()

class AnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    depth: str = Field("standard", pattern="^(standard|deep)$")


@app.post("/api/analysis", status_code=202)
async def request_analysis(
    req: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Pro tier check (Phase 3)
    # if not user.is_pro:
    #     raise HTTPException(403, detail={"error": "pro_required", ...})

    # Check for existing pending analysis for this ticker+user
    existing = db.query(AnalysisReport).filter(
        AnalysisReport.user_id == user.id,
        AnalysisReport.ticker == req.ticker,
        AnalysisReport.status.in_(["pending", "running"]),
    ).first()
    if existing:
        return {
            "analysis_id": existing.id,
            "status": existing.status,
            "ticker": req.ticker,
            "poll_url": f"/api/analysis/{existing.id}",
        }

    # Create the report row
    report = AnalysisReport(
        user_id=user.id,
        ticker=req.ticker,
        status="pending",
        config_json=json.dumps({"depth": req.depth}),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Launch background task
    background_tasks.add_task(service.run_analysis, req.ticker, report.id)

    return {
        "analysis_id": report.id,
        "status": "pending",
        "ticker": req.ticker,
        "estimated_seconds": 180,
        "poll_url": f"/api/analysis/{report.id}",
    }


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(AnalysisReport).filter(
        AnalysisReport.id == analysis_id,
        AnalysisReport.user_id == user.id,
    ).first()
    if not report:
        raise HTTPException(404, detail="Analysis not found")

    response = {
        "analysis_id": report.id,
        "status": report.status,
        "ticker": report.ticker,
    }
    if report.status == "completed":
        response["completed_at"] = report.completed_at
        response["result"] = json.loads(report.result_json)
    elif report.status == "failed":
        response["error"] = report.error_message
    return response


@app.get("/api/analysis/history")
async def get_analysis_history(
    ticker: str | None = None,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AnalysisReport).filter(AnalysisReport.user_id == user.id)
    if ticker:
        query = query.filter(AnalysisReport.ticker == ticker)
    reports = query.order_by(AnalysisReport.created_at.desc()).limit(limit).all()
    return {
        "analyses": [
            {
                "analysis_id": r.id,
                "ticker": r.ticker,
                "status": r.status,
                "rating": r.rating,
                "completed_at": r.completed_at,
            }
            for r in reports
        ]
    }
```

---

## 12. New SQLAlchemy Model

```python
# Added to backend/models.py

class AnalysisReport(Base):
    """An AI analysis run for a ticker, triggered by a user."""
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    # 'pending' | 'running' | 'completed' | 'failed'

    config_json = Column(String, nullable=True)
    result_json = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    rating = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="analysis_reports")
```

---

## 13. Frontend New Components

```
web/src/app/[locale]/analysis/
├── page.tsx                    # Analysis history list
└── [ticker]/
    └── page.tsx                # Trigger + view analysis for a stock

web/src/components/analysis/
├── AnalysisTrigger.tsx         # "تحليل بالذكاء الاصطناعي" button + Pro gate
├── AnalysisProgress.tsx        # Spinner with phase hints (Arabic)
├── RecommendationCard.tsx      # Rating badge + executive summary
├── DebateViewer.tsx            # Bull vs Bear expandable sections
├── AnalystTabs.tsx             # 4-tab analyst report viewer
├── RiskAssessment.tsx          # 3-way risk discussion
└── ShariaContextBadge.tsx      # Links analysis to existing Sharia verdict
```

---

## 14. Environment Variables (additions to Mizan's .env)

```env
# TradingAgents integration
TRADINGAGENTS_LLM_PROVIDER=openai
TRADINGAGENTS_DEEP_THINK_LLM=gpt-5.5
TRADINGAGENTS_QUICK_THINK_LLM=gpt-5.4-mini
# (API keys come from OPENAI_API_KEY or provider-specific vars)

# Analysis limits
ANALYSIS_DAILY_LIMIT=5          # max analyses per user per day
ANALYSIS_CONCURRENT_LIMIT=2     # max concurrent analyses globally
```

Dependencies (add to `backend/requirements.txt`):

```
tradingagents>=0.3.0    # or local path: -e ../tradingagents
```

---

## 15. Implementation Phases

### Phase 0 — Validate Data Coverage (prerequisite) ✦
**Goal**: Confirm TradingAgents works with Saudi tickers before building.

- [ ] Install TradingAgents locally: `pip install -e ../tradingagents`
- [ ] Test: `ta.propagate("2222.SR", "2025-01-15")` — does yfinance return data?
- [ ] If `.SR` tickers fail, investigate Tadawul data adapters or custom yfinance fixes
- [ ] Test 2-3 more tickers: `1180.SR` (Rajhi), `1120.SR` (STC), `2010.SR` (SABIC)
- [ ] Document which tickers work and which fail

### Phase 1 — Minimum Bridge (MVP)
**Goal**: One ticker → one analysis → rendered on screen (English only).

- [ ] Add `tradingagents` to backend dependencies
- [ ] Add `AnalysisReport` model to `models.py`
- [ ] Create `analysis_parser.py` (markdown field extraction)
- [ ] Create `analysis_service.py` (wraps `TradingAgentsGraph`)
- [ ] Add `POST /api/analysis` + `GET /api/analysis/{id}` to `app.py`
- [ ] Transform `final_state` → `AnalysisResult` JSON (English only)
- [ ] Frontend: `AnalysisTrigger` + polling + raw JSON render
- [ ] **No translation, no Pro gate, no history** — prove the pipe works end-to-end

### Phase 2 — Arabic + Structure
- [ ] Translation pass (LLM translates structured fields to Arabic)
- [ ] `RecommendationCard`, `DebateViewer`, `AnalystTabs`, `RiskAssessment` components
- [ ] Sharia context badge (pull verdict from existing screening)
- [ ] Analysis history page

### Phase 3 — Pro Tier + Polish
- [ ] `is_pro` field on User, subscription check middleware
- [ ] Rate limiting (daily/concurrent limits)
- [ ] Cache: if analysis for ticker was done in last 24h, serve cached result
- [ ] Email notification when long-running analysis completes
- [ ] "Deep analysis" option (more debate rounds, longer runtime)

### Phase 4 — Scale (if needed)
- [ ] Move TradingAgents to a separate worker process (Celery/RQ) if LLM calls block the API
- [ ] Analysis queue with priority for Pro users
- [ ] Pre-compute analyses for top Saudi stocks nightly (cron)
- [ ] WebSocket for real-time progress updates (replace polling)

---

## 16. Key Constraints & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **yfinance may not cover Saudi tickers (`.SR`)** | **Blocking** — no data means no analysis | Phase 0 validates before building. Fallback: Tadawul API or custom data adapter |
| TradingAgents takes 2-5 min per analysis | User experience | Background task from day one. Polling pattern. Estimated time shown to user. |
| LLM API costs per analysis ($0.05-0.50) | Business model | Rate-limit free tier, cache recent analyses, monitor cost |
| Markdown parsing is fragile | Data quality | Patterns are deterministic (`**Field**: value`), rendered by known functions. Unit test the parser against real output. |
| TradingAgentsGraph holds LLM clients in memory | Memory | Singleton pattern, lazy init, one instance per process |
| Concurrent analyses could exhaust API rate limits | API failures | Global semaphore limiting concurrent runs |
| Arabic translation adds latency + another LLM call | UX delay | Single batched call, translate only structured fields, cache translations |
| `propagate()` is synchronous/blocking | Event loop blocking | Run in `loop.run_in_executor()` thread pool |

---

## 17. What This Bridge Does NOT Do

- Does not modify TradingAgents' agent logic or prompts
- Does not modify Mizan's existing endpoints (new routes only)
- Does not require a second server/deployment (Phase 1-3 are in-process)
- Does not expose raw agent transcripts to users (structured summaries only)
- Does not auto-execute trades (TradingAgents is research, not execution)
- Does not set TradingAgents' `output_language` to Arabic (reasoning stays English for quality)
