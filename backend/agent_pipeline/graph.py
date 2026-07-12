"""LangGraph graph builder + ``run_pipeline`` entry point.

Wires all 12 Mizan agent nodes into a single compiled graph:

    Market Analyst → Fundamentals Analyst → News Analyst → Sharia Analyst
        → Bull Researcher ↔ Bear Researcher  (debate, MAX_DEBATE_ROUNDS)
        → Research Manager → Trader
        → Aggressive ↔ Conservative ↔ Neutral  (risk debate, MAX_RISK_DISCUSS_ROUNDS)
        → Portfolio Manager (final decision)

The graph is constructed with ``StateGraph(AgentState)`` and compiled once
per ``run_pipeline`` call.  ``run_pipeline`` pre-fetches all data, invokes
the graph, stores the decision in the memory log, and returns a dict.
"""

from __future__ import annotations

import logging
from datetime import datetime

from langgraph.graph import END, START, StateGraph

from agent_pipeline.analysts.fundamentals_analyst import fundamentals_analyst_node
from agent_pipeline.analysts.market_analyst import market_analyst_node
from agent_pipeline.analysts.news_analyst import news_analyst_node
from agent_pipeline.analysts.sharia_analyst import sharia_analyst_node
from agent_pipeline.config import (
    MAX_DEBATE_ROUNDS,
    MAX_RECUR_LIMIT,
    MAX_RISK_DISCUSS_ROUNDS,
    MEMORY_LOG_PATH,
)
from agent_pipeline.managers.portfolio_manager import create_portfolio_manager
from agent_pipeline.managers.research_manager import create_research_manager
from agent_pipeline.memory import MizanMemoryLog
from agent_pipeline.researchers.bear_researcher import create_bear_researcher
from agent_pipeline.researchers.bull_researcher import create_bull_researcher
from agent_pipeline.risk.aggressive import create_aggressive_risk_debator
from agent_pipeline.risk.conservative import create_conservative_risk_debator
from agent_pipeline.risk.neutral import create_neutral_risk_debator
from agent_pipeline.risk.trader import create_trader
from agent_pipeline.state import AgentState
from agent_pipeline.tools.data import (
    fetch_fundamentals_data,
    fetch_market_data,
    fetch_news_data,
    fetch_sharia_data,
    fetch_yfinance_financials,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conditional edge routers
# ---------------------------------------------------------------------------


def debate_router(state) -> str:
    """Route after a bull/bear debate turn.

    Each full round = bull speaks + bear speaks, so we need
    ``MAX_DEBATE_ROUNDS * 2`` total turns.  ``count`` is incremented by each
    researcher node, so the threshold is ``MAX_DEBATE_ROUNDS * 2``.
    """
    debate = state.get("investment_debate_state") or {}
    count = debate.get("count", 0)
    return "end" if count >= MAX_DEBATE_ROUNDS * 2 else "continue"


def risk_router(state) -> str:
    """Route after a risk-debate turn.

    Each full round = aggressive + conservative + neutral (3 turns), so the
    threshold is ``MAX_RISK_DISCUSS_ROUNDS * 3``.
    """
    debate = state.get("risk_debate_state") or {}
    count = debate.get("count", 0)
    return "end" if count >= MAX_RISK_DISCUSS_ROUNDS * 3 else "next"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph():
    """Construct and compile the Mizan 12-node LangGraph pipeline."""
    graph = StateGraph(AgentState)

    # ── Instantiate factory-based nodes ───────────────────────────────
    bull_researcher = create_bull_researcher()
    bear_researcher = create_bear_researcher()
    research_manager = create_research_manager()
    trader = create_trader()
    aggressive_debator = create_aggressive_risk_debator()
    conservative_debator = create_conservative_risk_debator()
    neutral_debator = create_neutral_risk_debator()
    portfolio_manager = create_portfolio_manager()

    # ── Add all 12 nodes ──────────────────────────────────────────────
    graph.add_node("market_analyst", market_analyst_node)
    graph.add_node("fundamentals_analyst", fundamentals_analyst_node)
    graph.add_node("news_analyst", news_analyst_node)
    graph.add_node("sharia_analyst", sharia_analyst_node)
    graph.add_node("bull_researcher", bull_researcher)
    graph.add_node("bear_researcher", bear_researcher)
    graph.add_node("research_manager", research_manager)
    graph.add_node("trader", trader)
    graph.add_node("aggressive_debator", aggressive_debator)
    graph.add_node("conservative_debator", conservative_debator)
    graph.add_node("neutral_debator", neutral_debator)
    graph.add_node("portfolio_manager", portfolio_manager)

    # ── Linear analyst chain ──────────────────────────────────────────
    graph.add_edge(START, "market_analyst")
    graph.add_edge("market_analyst", "fundamentals_analyst")
    graph.add_edge("fundamentals_analyst", "news_analyst")
    graph.add_edge("news_analyst", "sharia_analyst")
    graph.add_edge("sharia_analyst", "bull_researcher")

    # ── Bull ↔ Bear debate (conditional) ─────────────────────────────
    graph.add_conditional_edges(
        "bull_researcher",
        debate_router,
        {"continue": "bear_researcher", "end": "research_manager"},
    )
    graph.add_conditional_edges(
        "bear_researcher",
        debate_router,
        {"continue": "bull_researcher", "end": "research_manager"},
    )

    # ── Research Manager → Trader → Risk debate ───────────────────────
    graph.add_edge("research_manager", "trader")
    graph.add_edge("trader", "aggressive_debator")

    # ── Risk debate round-robin (conditional) ─────────────────────────
    #   aggressive → conservative → neutral → (loop or end)
    graph.add_conditional_edges(
        "aggressive_debator",
        risk_router,
        {"next": "conservative_debator", "end": "portfolio_manager"},
    )
    graph.add_conditional_edges(
        "conservative_debator",
        risk_router,
        {"next": "neutral_debator", "end": "portfolio_manager"},
    )
    graph.add_conditional_edges(
        "neutral_debator",
        risk_router,
        {"next": "aggressive_debator", "end": "portfolio_manager"},
    )

    # ── Final decision ───────────────────────────────────────────────
    graph.add_edge("portfolio_manager", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_pipeline(
    ticker: str,
    company_name: str = "",
    sector: str = "",
    financial_data: dict | None = None,
) -> dict:
    """Run the full Mizan agent pipeline for a single ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker (e.g. ``"2222.SR"`` for Saudi Aramco).
    company_name : str
        Human-readable company name (optional, improves LLM prompts).
    sector : str
        GICS-style sector name — used for Sharia qualitative screen.
    financial_data : dict | None
        Optional balance-sheet metrics for the Sharia quantitative screen
        (``total_assets``, ``total_debt``, ``interest_bearing_investments``,
        ``accounts_receivable``, ``cash_and_equivalents``, ``market_cap``,
        ``non_compliant_income``, ``total_revenue``).

    Returns
    -------
    dict
        ``{"decision", "market_report", "fundamentals_report", "news_report",
        "sharia_report", "investment_plan", "trader_investment_plan"}``
    """
    financial_data = financial_data or {}

    # ── Auto-detect company info and financials from yfinance ─────────
    yf_fin = fetch_yfinance_financials(ticker)
    if not company_name and yf_fin.get("company_name"):
        company_name = yf_fin["company_name"]
    if not sector and yf_fin.get("sector"):
        sector = yf_fin["sector"]

    # Merge: externally-provided financial_data takes priority over auto-fetched
    auto_raw = yf_fin.get("raw", {})
    merged_financials = {**auto_raw, **financial_data}

    graph = build_graph()

    # ── Pre-fetch all data before the first node runs ────────────────
    initial_state: dict = {
        "company_of_interest": ticker,
        "trade_date": datetime.now().strftime("%Y-%m-%d"),
        "messages": [],
        "instrument_context": None,  # will use default from get_instrument_context_from_state
        "price_data": fetch_market_data(ticker),
        "financial_data": fetch_fundamentals_data(ticker),
        "news_data": fetch_news_data(ticker),
        "sharia_data": fetch_sharia_data(ticker, sector=sector, **merged_financials),
        # Analyst reports — initialised empty, filled by each analyst
        "market_report": "",
        "fundamentals_report": "",
        "news_report": "",
        "sharia_report": "",
        # Bull/bear debate state
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
            "judge_decision": "",
            "count": 0,
        },
        "investment_plan": "",
        "trader_investment_plan": "",
        # Risk debate state
        "risk_debate_state": {
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "history": "",
            "latest_speaker": "",
            "current_aggressive_response": "",
            "current_conservative_response": "",
            "current_neutral_response": "",
            "judge_decision": "",
            "count": 0,
        },
        "final_trade_decision": "",
        "past_context": "",
    }

    # ── Load past memory context ─────────────────────────────────────
    try:
        memory = MizanMemoryLog(MEMORY_LOG_PATH)
        initial_state["past_context"] = memory.get_past_context(ticker)
    except Exception:
        logger.warning("Failed to load past memory context", exc_info=True)

    # ── Invoke the compiled graph ────────────────────────────────────
    result = graph.invoke(initial_state, {"recursion_limit": MAX_RECUR_LIMIT})

    # ── Store decision in memory log ──────────────────────────────────
    try:
        memory = MizanMemoryLog(MEMORY_LOG_PATH)
        memory.store_decision(
            ticker,
            initial_state["trade_date"],
            result.get("final_trade_decision", ""),
        )
    except Exception:
        logger.warning("Failed to store decision in memory log", exc_info=True)

    return {
        "decision": result.get("final_trade_decision", ""),
        "market_report": result.get("market_report", ""),
        "fundamentals_report": result.get("fundamentals_report", ""),
        "news_report": result.get("news_report", ""),
        "sharia_report": result.get("sharia_report", ""),
        "investment_plan": result.get("investment_plan", ""),
        "trader_investment_plan": result.get("trader_investment_plan", ""),
    }
