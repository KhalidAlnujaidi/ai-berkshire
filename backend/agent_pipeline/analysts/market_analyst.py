"""Market / technical analyst node for the Mizan pipeline.

Reads ``state['price_data']`` (pre-fetched by the graph's data-fetch layer),
asks the quick-think LLM for a concise technical-and-momentum read, and
writes ``state['market_report']``.  The report is consumed downstream by
the bull/bear researchers and the Research Manager.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_instrument_context_from_state, get_language_instruction

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a market analyst specialising in technical analysis, price action, and short-term market sentiment.

Your job: given price/market data for a single instrument, produce a focused **market report** (not a full investment thesis). Your downstream readers are bull/bear researchers and a portfolio manager — they need actionable technical signals, not a textbook.

Analyse:
- Recent price action: trend direction, momentum, and any notable moves (breakouts, reversals, gaps).
- Position within the 52-week range and 6-month high/low.
- Volume patterns if available.
- Short-term support/resistance levels you can infer from the data.
- Overall technical posture: bullish, bearish, or neutral, with specific evidence.

Be concrete and cite numbers from the data. Avoid generic statements like "the stock is volatile" — say "the stock traded in a 12% range over 6 months with a downward drift from X to Y."

Do NOT produce a buy/sell recommendation — that is the portfolio manager's job. Focus purely on what the price action is telling you."""


def market_analyst_node(state) -> dict:
    """Generate the market/technical analyst report from price data.

    Args:
        state: LangGraph ``AgentState`` with at least ``company_of_interest``
            and ``price_data`` populated.

    Returns:
        Dict update with ``market_report`` (the report text) and a
        ``messages`` list containing the report as a ``HumanMessage`` so
        downstream agents can read it via the shared message log.
    """
    logger.info("Market analyst: starting analysis for %s", state.get("company_of_interest"))

    llm = get_quick_llm()
    ticker = state["company_of_interest"]
    instrument_ctx = get_instrument_context_from_state(state)
    lang_instruction = get_language_instruction()

    price_data = state.get("price_data", "[No price data available]")

    human_content = (
        f"{instrument_ctx}\n\n"
        f"Analyse the market/technical picture for **{ticker}**.\n\n"
        f"## Market & Price Data\n{price_data}\n\n"
        f"Produce your market report now.{lang_instruction}"
    )

    prompt = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    response = llm.invoke(prompt)
    report = response.content

    logger.info("Market analyst: completed report for %s (%d chars)", ticker, len(report))

    return {
        "market_report": report,
        "messages": [HumanMessage(content=report)],
    }
