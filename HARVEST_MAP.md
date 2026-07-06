# Mizan Harvest Map — What to Steal from TradingAgents & Vibe-Trading

> Generated from deep code-graph analysis of both reference projects.
> TradingAgents: 1,373 nodes, 5,136 edges, 130 Python files
> Vibe-Trading: 15,657 nodes, 59,052 edges, 986 Python + 52 TS files

---

## Executive Summary

Both projects solve **multi-agent investment analysis**, but at very different scales:

| Dimension | TradingAgents | Vibe-Trading | Mizan Today |
|---|---|---|---|
| Architecture | LangGraph state machine | ReAct loop + Swarm DAG | Single `research_engine.py` |
| Agent count | 10 fixed agents | N agents from presets | 0 |
| Data sources | 6 vendors, fallback chains | 50+ tools | Tadawul scraper only |
| Frontend | CLI only | React/Vite, SSE, charts | Next.js (basic) |
| Backtesting | No | Full engine (engines, metrics, optimizers) | No |
| Memory/learning | Markdown memory log | Persistent memory + hypothesis tracking | No |
| Paper trading | No | Shadow account system | No |
| Complexity | Moderate, clean, portable | Massive, opinionated, coupled |

**Verdict:** TradingAgents is the **architecture blueprint** (clean, portable patterns).
Vibe-Trading is the **feature wishlist** (what a mature product looks like).
Harvest the agent pipeline from TradingAgents; cherry-pick specific tools/features from Vibe-Trading.

---

## TIER 1 — High-Value, Portable, Immediate

### 1. Multi-Agent Analysis Pipeline (from TradingAgents)

**What it is:** A LangGraph state machine that chains analysts → debate → decision.
**Why Mizan needs it:** Replaces `research_engine.py` (single function) with a defensible AI pipeline.

**The pipeline:**
```
[Analysts]                    [Research]              [Risk Debate]              [Decision]
market_analyst    ─┐                              aggressive_debator  ─┐
news_analyst      ─┼─→ research_manager ─┐       conservative_debator ─┼─→ portfolio_manager
sentiment_analyst ─┤   (synthesizes)      ├─→ trader ─┤               │   (final call)
fundamentals      ─┤                      │          └─→ neutral ─────┘
social_media      ─┘                      │
                    └─→ bull_researcher ──┤
                    └─→ bear_researcher ──┘
```

**Key files to port:**
- `tradingagents/tradingagents/graph/trading_graph.py` — orchestrator (the `TradingAgentsGraph` class)
- `tradingagents/tradingagents/graph/setup.py` — graph wiring
- `tradingagents/tradingagents/graph/conditional_logic.py` — debate round routing
- `tradingagents/tradingagents/agents/analysts/*.py` — 5 analyst nodes
- `tradingagents/tradingagents/agents/managers/*.py` — research manager + portfolio manager
- `tradingagents/tradingagents/agents/risk_mgmt/*.py` — 3 debators
- `tradingagents/tradingagents/agents/researchers/*.py` — bull/bear
- `tradingagents/tradingagents/agents/trader/trader.py` — trader node
- `tradingagents/tradingagents/agents/schemas.py` — structured output types

**Mizan adaptation needed:**
- Add **Sharia compliance screening** as a 6th analyst (using existing `sharia_screener.py`)
- Add **Tadawul/market context** analyst for Saudi-specific factors
- Replace global benchmarks (SPY) with Tadawul index (TASI)
- Arabic output language support (config already supports `output_language`)
- Filter out non-Sharia-compliant instruments before analysis

**Effort:** ~3-5 days. The agent code is clean, self-contained, and uses LangChain/LangGraph.

---

### 2. Memory & Learning System (from TradingAgents)

**What it is:** A markdown-based trading memory log that stores past decisions + outcomes.
**Why Mizan needs it:** Let the system learn from past calls — "this stock was flagged non-compliant last time."

**Key files:**
- `tradingagents/tradingagents/agents/utils/memory.py` — `TradingMemoryLog` class
- Key methods: `store_decision`, `load_entries`, `get_past_context`

**How it works:**
- Each analysis run stores: ticker, decision, reasoning, date
- Before each new run, loads relevant past context
- Feeds "lessons learned" into the portfolio manager prompt

**Effort:** ~1 day. Self-contained, no heavy deps.

---

### 3. Multi-Vendor Data Flow with Fallback (from TradingAgents)

**What it is:** A clean interface layer that routes data requests to vendors with ordered fallback.
**Why Mizan needs it:** Right now Mizan has `tadawul_scraper.py` (single point of failure).

**Key files:**
- `tradingagents/tradingagents/dataflows/interface.py` — `route_to_vendor`
- `tradingagents/tradingagents/dataflows/config.py` — vendor configuration
- `tradingagents/tradingagents/dataflows/y_finance.py` — yfinance adapter
- `tradingagents/tradingagents/dataflows/market_data_validator.py` — data quality checks

**Mizan adaptation:**
- Primary: Tadawul API (existing scraper)
- Fallback: yfinance for dual-listed Saudi stocks
- Add: Saudi macro data (SAMA rates, oil prices)
- Add: News sources (Argaam, Mubasher, Saudi Gazette)

**Effort:** ~2 days.

---

### 4. Structured Output for Decisions (from TradingAgents)

**What it is:** LangChain's `with_structured_output` producing typed `PortfolioDecision` objects.
**Why Mizan needs it:** Clean JSON decisions instead of free-text — better for UI + storage.

**Key files:**
- `tradingagents/tradingagents/agents/schemas.py` — `PortfolioDecision`, `TraderProposal`
- `tradingagents/tradingagents/agents/utils/structured.py` — `bind_structured`, `invoke_structured_or_freetext`

**Mizan-specific schema additions:**
- `sharia_score: float` — compliance score 0-100
- `sharia_issues: list[str]` — specific violations found
- `zakat_obligation: float` — estimated Zakat due
- `purification_required: bool` — if income purification needed

**Effort:** ~0.5 days.

---

## TIER 2 — High-Value, Moderate Effort

### 5. Frontend Chat/Streaming UI (from Vibe-Trading)

**What it is:** React-based chat interface with SSE streaming, agent avatars, progress bars, tool indicators.
**Why Mizan needs it:** Currently Mizan's research is "click button, wait, see result." Vibe-Trading shows real-time agent reasoning.

**Key components:**
- `Vibe-Trading/frontend/src/components/chat/` — AgentAvatar, ProgressBar, ToolProgressIndicator, WelcomeScreen
- `Vibe-Trading/frontend/src/hooks/useSSE.ts` — SSE hook for streaming
- `Vibe-Trading/frontend/src/components/charts/` — CandlestickChart, EquityChart, CorrelationMatrix, ValidationPanel

**Note:** Vibe-Trading uses React/Vite, Mizan uses Next.js. Components need porting to Next.js, but logic/patterns transfer directly.

**Effort:** ~5-7 days (porting + adaptation).

---

### 6. Backtesting Engine (from Vibe-Trading)

**What it is:** Full backtesting framework with engines, metrics, benchmarking, correlation analysis, optimizers.
**Why Mizan needs it:** Let users see "if you'd followed Mizan's recommendations for the last year, here's your return."

**Key files:**
- `Vibe-Trading/agent/src/` (backtest module) — `engines/`, `metrics.py`, `benchmark.py`, `correlation.py`, `optimizers/`, `validation.py`, `run_card.py`, `runner.py`

**Effort:** ~5-7 days. Heavy module, needs careful extraction from Vibe-Trading's framework.

---

### 7. Paper Trading / Shadow Account (from Vibe-Trading)

**What it is:** Virtual portfolio that tracks recommendations without real money.
**Why Mizan needs it:** Users want to test before they trust. Drahim has this implicitly.

**Key files:**
- `Vibe-Trading/agent/src/shadow_account/` — full virtual portfolio system

**Effort:** ~3-4 days.

---

### 8. Scheduled Research Jobs (from Vibe-Trading)

**What it is:** Cron-like system that runs research automatically and pushes alerts.
**Why Mizan needs it:** Users get "your portfolio was re-analyzed overnight, 2 new recommendations."

**Key files:**
- `Vibe-Trading/agent/src/scheduled_research/` — `store.py`, job scheduling
- `Vibe-Trading/agent/src/channels/` — notification channels

**Effort:** ~2-3 days. Pairs well with Mizan's existing alerts.

---

## TIER 3 — Strategic, Long-Term

### 9. Swarm DAG Orchestration (from Vibe-Trading)

**What it is:** Multi-agent DAG runtime — tasks scheduled by topological layers, parallel within each layer.
**Why it matters:** When Mizan has 10+ agents analyzing a full portfolio simultaneously, this is how you scale.

**Key files:**
- `Vibe-Trading/agent/src/swarm/runtime.py` — `SwarmRuntime` class
- `Vibe-Trading/agent/src/swarm/task_store.py` — DAG validation, topological sort
- `Vibe-Trading/agent/src/swarm/worker.py` — worker execution
- `Vibe-Trading/agent/src/swarm/grounding.py` — preset → task resolution

**Verdict:** Don't port yet. Adopt after Tier 1 is working and you have ≥5 agents. The TradingAgents LangGraph pipeline handles parallelism adequately for now.

---

### 10. ReAct Agent Loop with 5-Layer Context (from Vibe-Trading)

**What it is:** Sophisticated context window management — microcompact, context collapse, auto-compact, compact tool, iterative update.
**Why it matters:** Prevents context overflow on long analysis sessions. 

**Key file:** `Vibe-Trading/agent/src/agent/loop.py`

**Verdict:** The technique is valuable but the implementation is tightly coupled. Learn the **patterns** (5-layer compaction), implement in Mizan's own loop when needed.

---

### 11. Hypothesis Tracking (from Vibe-Trading)

**What it is:** System that tracks investment hypotheses over time — "I predicted X because Y, here's what happened."
**Why it matters:** Unique feature that neither Drahim nor Malaa has. Shows users the AI is learning.

**Key files:**
- `Vibe-Trading/agent/src/hypotheses/` — `registry.py`, hypothesis lifecycle

**Verdict:** Strong differentiator. Port after Tier 1+2 is live.

---

## What NOT to Port

| Feature | Why Skip |
|---|---|
| Vibe-Trading's MCP server | Mizan is a SaaS, not a tool server |
| Vibe-Trading's 50+ market tools | Most are US/China market specific |
| Vibe-Trading's skill system | Overkill for Mizan's scope |
| TradingAgents' Reddit/StockTwits | Not relevant for Saudi market |
| TradingAgents' Polymarket integration | Prediction markets not relevant |

---

## Recommended Implementation Order

```
Phase 1 (Week 1-2): Foundation
  └─ Port TradingAgents pipeline → Mizan backend
     ├─ Agent framework (LangGraph)
     ├─ Sharia analyst (new)
     ├─ Tadawul data adapters
     └─ Structured decision output

Phase 2 (Week 3-4): Memory & Intelligence
  └─ Port memory log + multi-vendor data flow
     ├─ Trading memory (decisions + outcomes)
     ├─ Fallback data sources
     └─ News/macro integration

Phase 3 (Week 5-6): UI Upgrade
  └─ Port Vibe-Trading frontend patterns to Next.js
     ├─ SSE streaming for agent reasoning
     ├─ Chat-style analysis view
     └─ Charts (candlestick, equity)

Phase 4 (Week 7-8): Differentiation
  └─ Paper trading + scheduled research + hypothesis tracking
     ├─ Shadow account (virtual portfolio)
     ├─ Overnight automated re-analysis
     └─ Hypothesis tracking dashboard
```

---

## Dependencies Required

From TradingAgents:
- `langgraph` — state machine orchestration
- `langchain` — LLM abstraction
- `langchain-openai` / `langchain-google-genai` — providers
- `yfinance` — stock data fallback

From Vibe-Trading:
- `fastapi` (already in Mizan)
- `sse-starlette` — server-sent events
- Chart libs: `recharts` or `lightweight-charts` (frontend)
